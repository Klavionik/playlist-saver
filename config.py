from pydantic import BaseSettings


class Config(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    REDIRECT_URI: str
    SCOPE: str
    BASE_API_URL: str = 'https://api.spotify.com/v1'
    SECRET_KEY: str


config = Config()
