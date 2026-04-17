from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    app_env: str = "development"
    frontend_public_url: str = "http://localhost:3002"
    backend_public_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:3002,http://127.0.0.1:3002"
    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 8000

    database_url: str = "postgresql+asyncpg://crm_user:change_me@db:5432/crm_db"
    secret_key: str = "CHANGE_ME_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_redirect_uri: Optional[str] = None

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"

    app_port: int = 8000
    db_host: str = ""
    db_port: int = 5432
    redis_host: str = ""
    redis_port: int = 6379

    @model_validator(mode="after")
    def derive_feishu_redirect_uri(self):
        if not self.feishu_redirect_uri:
            self.feishu_redirect_uri = (
                self.frontend_public_url.rstrip("/") + "/auth/feishu/callback"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
