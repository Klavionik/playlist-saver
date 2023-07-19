import enum

from config import Config, get_config
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request, responses
from spotify import Client, get_client, get_scope
from starlette.templating import Jinja2Templates
from utils import HEADER_ROW, Playlist, delete_temp_file, save_playlist_as_csv


def version_context(_) -> dict:
    return {"version": get_config().APP_VERSION}


router = APIRouter()
templates = Jinja2Templates("templates", context_processors=[version_context])


class PlaylistScope(str, enum.Enum):
    ALL = "all"
    PUBLIC = "public"


@router.get("/", response_class=responses.HTMLResponse)
async def index(request: Request, config: Config = Depends(get_config)):
    token = request.session.get(config.TOKEN_KEY)

    if token:
        return responses.RedirectResponse("/playlists")
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login")
async def login(
    request: Request,
    scope: PlaylistScope,
    spotify: Client = Depends(get_client),
    config: Config = Depends(get_config),
):
    auth_scope = get_scope(public_playlists=scope == PlaylistScope.PUBLIC)

    async with spotify:
        url, state = spotify.authorize(auth_scope)
        request.session[config.STATE_KEY] = state
    return responses.RedirectResponse(url)


@router.get("/callback")
async def callback(
    request: Request,
    error: str | None = None,
    spotify: Client = Depends(get_client),
    config: Config = Depends(get_config),
):
    if error:
        return responses.RedirectResponse("/")

    state = request.session.pop(config.STATE_KEY)

    async with spotify:
        token = await spotify.fetch_token(str(request.url), state)
        spotify.save_token(token)

    return responses.RedirectResponse("/playlists")


@router.get("/playlists")
async def get_playlists(request: Request, spotify: Client = Depends(get_client)):
    async with spotify:
        data = await spotify.get_user()
        username = data.get("display_name")
        user_id = data.get("id")

        data = await spotify.get_playlists(user_id)
        items = data.get("items")
        playlists = [Playlist(item) for item in items]

    ctx = {"request": request, "username": username, "playlists": playlists}

    return templates.TemplateResponse("playlists.html", ctx)


@router.get("/playlists/{id}-{name}")
async def get_playlist_details(
    tasks: BackgroundTasks,
    spotify: Client = Depends(get_client),
    _id: str = Path(..., alias="id"),
    name: str = Path(...),
):
    async with spotify:
        items = []
        page = 0
        data = await spotify.get_tracks(_id)
        items += data.get("items")
        total = data.get("total")

        while len(items) < total:
            page += 1
            data = await spotify.get_tracks(_id, page=page)
            items += data.get("items")

    filepath = save_playlist_as_csv(HEADER_ROW, items)
    tasks.add_task(delete_temp_file, filepath)
    response = responses.FileResponse(filepath, media_type="text/csv", filename=f"{name}.csv")
    return response


@router.get("/logout")
async def logout(request: Request, config: Config = Depends(get_config)):
    request.session.pop(config.TOKEN_KEY)
    return responses.RedirectResponse("/")
