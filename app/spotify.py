import logging
from enum import Enum
from functools import wraps
from typing import Callable, Dict, List
from urllib.parse import urlencode

import attrs
import fastapi
import httpx
from authlib.integrations import httpx_client
from config import Config, get_config
from fastapi import Depends
from httpx import Response

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())


async def log_request(req: httpx.Request):
    log.info("Request: %s %s", req.method, req.url)


def request(f: Callable) -> Callable:
    @wraps(f)
    async def wrapper(*args, **kwargs) -> Dict:
        response = await f(*args, **kwargs)
        response.raise_for_status()
        return response.json()

    return wrapper


class ScopeItem(str, Enum):
    USER_READ_PRIVATE = "user-read-private"
    USER_READ_EMAIL = "user-read-email"
    PLAYLIST_READ_COLLABORATIVE = "playlist-read-collaborative"
    PLAYLIST_READ_PRIVATE = "playlist-read-private"


@attrs.define
class Scope:
    _scope: List[ScopeItem] = attrs.Factory(list)

    def add_scopes(self, *scope: ScopeItem):
        self._scope.extend(scope)

    def remove_scope(self, scope: ScopeItem):
        try:
            self._scope.remove(scope)
        except ValueError:
            pass

    def get_scope(self):
        return " ".join(self._scope)

    def __str__(self):
        return self.get_scope()


@attrs.define
class Client:
    base_url: str
    token_endpoint: str
    client_id: str
    client_secret: str
    token: Dict | None
    token_key: str
    bound_request: fastapi.Request
    session: httpx_client.AsyncOAuth2Client | None = None
    tracks_limit: int = 50

    async def __aenter__(self):
        self.session = httpx_client.AsyncOAuth2Client(
            base_url=self.base_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self._get_redirect_uri(),
            token=self.token,
            update_token=self._update_token,
            token_endpoint=self.token_endpoint,
            event_hooks={"request": [log_request]},
        )
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)
        self.session = None

    def authorize(self, scope: Scope):
        self.session.scope = scope
        return self.session.create_authorization_url("https://accounts.spotify.com/authorize")

    async def fetch_token(self, auth_response: str, state: str):
        self.session.state = state
        return await self.session.fetch_token(authorization_response=auth_response)

    @request
    async def get_user(self) -> Response:
        return await self.session.get("/me")

    @request
    async def get_playlists(self, user_id: str) -> Response:
        return await self.session.get(f"/users/{user_id}/playlists")

    @request
    async def get_tracks(self, playlist_id: str, page: int = 0) -> Response:
        query = urlencode({"offset": self.tracks_limit * page, "limit": self.tracks_limit})
        return await self.session.get(f"/playlists/{playlist_id}/tracks?{query}")

    def save_token(self, token: Dict):
        self.bound_request.session[self.token_key] = token

    async def _update_token(self, token, *_, **__):
        self.save_token(token)

    def _get_redirect_uri(self):
        return str(self.bound_request.url_for("callback"))


def get_scope(public_playlists: bool):
    scopes = list(ScopeItem)

    if public_playlists:
        scopes.remove(ScopeItem.PLAYLIST_READ_PRIVATE)
        scopes.remove(ScopeItem.PLAYLIST_READ_COLLABORATIVE)

    return scopes


def get_client(req: fastapi.Request, config: Config = Depends(get_config)) -> Client:
    token = req.session.get(config.TOKEN_KEY)
    return Client(
        base_url=config.BASE_API_URL,
        token_endpoint=config.TOKEN_ENDPOINT,
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        token=token,
        token_key=config.TOKEN_KEY,
        bound_request=req,
    )
