from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
        case_sensitive=False,
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_STORE_URL: str = "http://localhost:5173"
    FRONTEND_ADMIN_URL: str = "http://localhost:5174"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()