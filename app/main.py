# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.database.postgres_user import PostgresUserRepository
from app.routers.v1 import health
from app.routers.v1 import user

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Engine async PostgreSQL (richiede asyncpg installato)
        engine = create_async_engine(
            settings.postgres_dsn,  # es: "postgresql+asyncpg://user:pass@user-db:5432/userdb"
            pool_pre_ping=True,
        )

        # Repository utenti e bootstrap schema (in produzione usa Alembic)
        user_repo = PostgresUserRepository(engine)
        await user_repo.ensure_schema()
        app.state.user_repo = user_repo  # usato da get_user_repository()

        try:
            yield
        finally:
            await engine.dispose()

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
