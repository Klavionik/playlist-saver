from config import config
from fastapi import FastAPI
from routes import router
from starlette.middleware.sessions import SessionMiddleware


def create_app():
    app = FastAPI(debug=config.DEBUG)
    app.include_router(router)
    app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
    return app
