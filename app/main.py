from authlib.integrations.base_client.errors import OAuthError
from config import config
from fastapi import FastAPI, Request, responses
from routes import router
from starlette.middleware.sessions import SessionMiddleware


async def handle_oauth_error(request: Request, exc: OAuthError):
    request.session.pop(config.TOKEN_KEY, None)
    request.session[config.ERROR_KEY] = exc.description
    return responses.RedirectResponse("/")


def create_app():
    app = FastAPI(debug=config.DEBUG)
    app.include_router(router)
    app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
    app.add_exception_handler(OAuthError, handle_oauth_error)
    return app
