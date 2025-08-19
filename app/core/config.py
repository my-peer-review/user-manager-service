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
    mongo_uri: str
    mongo_db_name: str

    class Config:
        env_file = None  # solo ENV vars

settings = Settings()
