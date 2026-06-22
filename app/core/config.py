from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=str(ENV_FILE_PATH),
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

    
    MP_ACCESS_TOKEN: str = ""
    MP_PUBLIC_KEY: str = ""
    MP_NOTIFICATION_URL: str = ""


    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()