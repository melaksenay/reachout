#pydantic basesettings for env vars.
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # These attributes must exactly match the keys in your .env file
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    MY_HANDLE: str = ""  # TikTok handle for filtering out myself
    SUPABASE_AUTH_REDIRECT: str = ""  # OAuth redirect URL (planned)
    # model_config tells Pydantic exactly how to load the variables
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiate the settings object to be imported by other files
@lru_cache()
def get_settings() -> Settings:
    return Settings()
    