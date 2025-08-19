# app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = os.getenv("ENV", "unit-test")

    # JWT
    jwt_algorithm: str
    jwt_public_key: str   # contiene direttamente la chiave
    jwt_private_key: str  # contiene direttamente la chiave

    # Postgres
    postgres_dsn: str     # es: "postgresql+asyncpg://user:pass@host:5432/dbname"

    class Config:
        env_file = None  # solo ENV vars

settings = Settings()
