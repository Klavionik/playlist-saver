from fastapi import APIRouter, responses, Request, BackgroundTasks, Depends, Path
from starlette.templating import Jinja2Templates

from config import Config, get_config
from spotify import Client, Scope, get_scopes, get_client
from utils import delete_temp_file, save_playlist_as_csv, HEADER_ROW, Playlist

router = APIRouter()
templates = Jinja2Templates('templates')


@router.get('/', response_class=responses.HTMLResponse)
async def index(request: Request, config: Config = Depends(get_config)):
    token = request.session.get(config.TOKEN_KEY)

    if token:
        return responses.RedirectResponse('/playlists')
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/login')
async def login(
        request: Request,
        collaborative: bool = False,
        private: bool = False,
        spotify: Client = Depends(get_client),
        config: Config = Depends(get_config)
):
    scope = Scope()
    scope.add_scopes(*get_scopes(collaborative, private))

    async with spotify:
        url, state = spotify.authorize(scope)
        request.session[config.STATE_KEY] = state
    return responses.RedirectResponse(url)


@router.get('/callback')
async def callback(
        request: Request,
        error: str | None = None,
        spotify: Client = Depends(get_client),
        config: Config = Depends(get_config)
):
    if error:
        return responses.RedirectResponse('/')

    state = request.session.get(config.STATE_KEY)

    async with spotify:
        token = await spotify.fetch_token(str(request.url), state)

    request.session[config.TOKEN_KEY] = token
    request.session.pop(config.STATE_KEY)
    return responses.RedirectResponse('/playlists')


@router.get('/playlists')
async def get_playlists(request: Request, spotify: Client = Depends(get_client)):
    async with spotify:
        data = await spotify.get_user()
        username = data.get('display_name')
        user_id = data.get('id')

        data = await spotify.get_playlists(user_id)
        items = data.get('items')
        playlists = [Playlist(item) for item in items]

    ctx = {'request': request, 'username': username, 'playlists': playlists}

    return templates.TemplateResponse('playlists.html', ctx)


@router.get('/playlists/{id}-{name}')
async def get_playlist_details(
        tasks: BackgroundTasks,
        spotify: Client = Depends(get_client),
        _id: str = Path(..., alias='id'),
        name: str = Path(...),
):
    async with spotify:
        items = []
        page = 0
        data = await spotify.get_tracks(_id)
        items += data.get('items')
        total = data.get('total')

        while len(items) < total:
            page += 1
            data = await spotify.get_tracks(_id, page=page)
            items += data.get('items')

    filepath = save_playlist_as_csv(HEADER_ROW, items)
    tasks.add_task(delete_temp_file, filepath)
    response = responses.FileResponse(filepath, media_type='text/csv', filename=f'{name}.csv')
    return response


@router.get('/logout')
async def logout(request: Request, config: Config = Depends(get_config)):
    request.session.pop(config.TOKEN_KEY)
    return responses.RedirectResponse('/')


def get_router():
    return router
