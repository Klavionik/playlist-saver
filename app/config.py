from pydantic_settings import BaseSettings


class Config(BaseSettings):
    APP_VERSION: str = ""
    DEBUG: bool = False
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    BASE_API_URL: str = "https://api.spotify.com/v1"
    TOKEN_ENDPOINT: str = "https://accounts.spotify.com/api/token"
    SECRET_KEY: str = ""
    STATE_KEY: str = "_spotify_state"
    TOKEN_KEY: str = "_spotify_token"
    REFRESH_TOKEN_KEY: str = "_spotify_refresh_token"


config = Config()


def get_config():
    return config
