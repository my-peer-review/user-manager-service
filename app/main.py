# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.database.mongo_user import MongoUserRepository
from app.routers.v1 import health
from app.routers.v1 import user

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
        db = client[settings.mongo_db_name]
        repo = MongoUserRepository(db)
        await repo.ensure_indexes()
        app.state.user_repo = repo       # <-- usato da get_repository()
        yield
        client.close()

    app = FastAPI(
        title="User Manager Microservice",
        description="Microservizio per gestione utenti e JWT (register/login/me)",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Router
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(user.router,   prefix="/api/v1", tags=["user"])

    return app


app = create_app()
