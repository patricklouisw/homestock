""" Config.py
Read DATABASE_URL out ot.env, validate it exists, and expose it to the rest of the app as a python object.

"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Values the app needs at runtime, read from .env or the environment"""

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    test_database_url: str
    sql_echo: bool = False

settings = Settings() # type: ignore[call-arg]