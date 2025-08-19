# app/database/postgres_user.py
from typing import Optional
from sqlalchemy import MetaData, Table, Column, Integer, String, Text, UniqueConstraint, insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from app.database.user_repo import UserRepo
from app.schemas.user import UserCreate, User


metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(50), nullable=False, unique=True, index=True),
    Column("email", String(255), nullable=True, unique=True, index=True),
    Column("role", String(32), nullable=False),
    Column("hashed_password", Text, nullable=False),
    UniqueConstraint("username", name="uq_users_username"),
    UniqueConstraint("email", name="uq_users_email"),
)

def _map_user(row) -> User:
    return User(userId=row["id"], username=row["username"], email=row["email"], role=row["role"])

def _map_row(row: Optional[dict]) -> Optional[User]:
    if not row:
        return None
    return User(
        userId=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
    )

class PostgresUserRepository(UserRepo):
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def ensure_schema(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def create(self, data: UserCreate, *, hashed_password: str) -> int:
        stmt = (
            insert(users)
            .values(
                username=data.username,
                email=data.email,
                role=data.role,
                hashed_password=hashed_password,
            )
            .returning(users.c.id)
        )
        async with self.session_factory() as session:
            res = await session.execute(stmt)
            new_id: int = res.scalar_one()
            await session.commit()
            return new_id

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(users).where(users.c.id == user_id)
        async with self.session_factory() as session:
            res = await session.execute(stmt)
            row = res.mappings().first()
            return _map_row(row) if row else None

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(users).where(users.c.username == username)
        async with self.session_factory() as session:
            res = await session.execute(stmt)
            row = res.mappings().first()
            return _map_row(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(users).where(users.c.email == email)
        async with self.session_factory() as session:
            res = await session.execute(stmt)
            row = res.mappings().first()
            return _map_row(row) if row else None

    async def get_auth_by_email(self, email: str):
        stmt = select(users).where(users.c.email == email)
        async with self.session_factory() as session:
            res = await session.execute(stmt)
            row = res.mappings().first()
            if not row: return None
            return _map_user(row), row["hashed_password"]

