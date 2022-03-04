import httpx
import tempfile
import csv
import os
from datetime import datetime, timedelta
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import FastAPI, responses, Request, Cookie, BackgroundTasks
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import config

STATE_KEY = '_spotify_state'
TOKEN_KEY = '_spotify-token'

app = FastAPI(debug=True)
templates = Jinja2Templates('templates')
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)


def clean_temp_file(path: str):
    print('deleting', path)
    if os.path.exists(path):
        os.remove(path)


@app.get('/', response_class=responses.HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/login')
async def login():
    authorize_url = 'https://accounts.spotify.com/authorize'
    client = AsyncOAuth2Client(
        client_id=config.CLIENT_ID,
        scope=config.SCOPE,
        redirect_uri=config.REDIRECT_URI
    )
    url, state = client.create_authorization_url(authorize_url)
    response = responses.RedirectResponse(url)
    response.set_cookie(STATE_KEY, state)
    return response


@app.get('/callback')
async def callback(request: Request, stored_state: str = Cookie('', alias=STATE_KEY)):
    token_url = 'https://accounts.spotify.com/api/token'

    client = AsyncOAuth2Client(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        state=stored_state
    )
    await client.fetch_token(token_url, authorization_response=str(request.url))
    request.session[TOKEN_KEY] = client.token.get('access_token')
    return responses.RedirectResponse('/playlists')


@app.get('/playlists')
async def get_playlists(request: Request):
    access_token = request.session.get(TOKEN_KEY)

    if not access_token:
        return "No access token"

    me_url = config.BASE_API_URL + '/me'

    async with httpx.AsyncClient(headers={'Authorization': f'Bearer {access_token}'}) as client:
        response: httpx.Response = await client.get(me_url)
        data = response.json()
        username = data.get('display_name')
        user_id = data.get('id')
        playlists_url = config.BASE_API_URL + f'/users/{user_id}/playlists'
        response: httpx.Response = await client.get(playlists_url)
        data = response.json()
        items = data.get('items')
        playlists = [(playlist['id'], playlist['name']) for playlist in items]

    ctx = {'request': request, 'username': username, 'playlists': playlists}

    return templates.TemplateResponse('playlists.html', ctx)


@app.get('/playlists/{id}:{playlist}')
async def get_playlist_details(request: Request, id: str, playlist: str, tasks: BackgroundTasks):
    access_token = request.session.get(TOKEN_KEY)

    if not access_token:
        return "No access token"

    tracks_url = config.BASE_API_URL + f'/playlists/{id}/tracks'
    filename = f'{playlist}.csv'

    async with httpx.AsyncClient(headers={'Authorization': f'Bearer {access_token}'}) as client:
        response = await client.get(tracks_url)
        data = response.json()
        items = data.get('items')

        with tempfile.NamedTemporaryFile(mode='wt', delete=False) as fh:
            tasks.add_task(clean_temp_file, fh.name)
            writer = csv.writer(fh)
            writer.writerow(('Track', 'Artist', 'Album', 'Added by', 'Date added', 'Duration'))

            for item in items:
                track = item['track']['name']
                artist = ', '.join([record['name'] for record in item['track']['artists']])
                album = item['track']['album']['name']
                added_by = item['added_by']['id']
                added_at = str(datetime.fromisoformat(item['added_at'].rstrip('Z')))
                duration_ms = timedelta(milliseconds=item['track']['duration_ms'])
                duration = f'{duration_ms.seconds // 60}:{duration_ms.seconds % 60}'

                writer.writerow((track, artist, album, added_by, added_at, duration))

            response = responses.FileResponse(fh.name, media_type='text/csv', filename=filename)
            return response
