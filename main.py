from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from config import config
from routes import router


def create_app():
    app = FastAPI(debug=config.DEBUG)
    app.include_router(router)
    app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
    return app
