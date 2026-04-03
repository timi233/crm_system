from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://crm_user:change_me@db:5432/crm_db"
    secret_key: str = "CHANGE_ME_SECRET_KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_redirect_uri: str = "http://localhost:3002/auth/feishu/callback"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"

    app_port: int = 8000
    db_host: str = ""
    db_port: int = 5432
    redis_host: str = ""
    redis_port: int = 6379

    class Config:
        env_file = ".env"
        extra = "allow"


def get_settings() -> Settings:
    return Settings()
