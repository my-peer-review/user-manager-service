from datetime import datetime, timezone
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import random

from app.database.user_repo import UserRepo
from app.schemas.user import UserCreate, User

def create_user_id() -> str:
    # genera un numero tra 10000 e 99999
    return f"us-{random.randint(00000, 99999)}"

class MongoUserRepository(UserRepo):
    """Implementazione MongoDB del repository utenti.

    Schema della collection `users` (document-based):
      - userId: str (UUID v4) — chiave applicativa
      - createdAt: datetime (UTC)
      - username: str (unique, indicizzato)
      - email: Optional[str] (unique, indicizzato se presente)
      - role: str
      - hashed_password: str
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["users"]

    # ----------------------
    # Mappers
    # ----------------------
    def _from_doc(self, d: dict) -> User:
        return User(
            userId=str(d["userId"]),
            username=d["username"],
            email=d.get("email"),
            role=d["role"],
        )

    def _to_doc(self, user_id: str, data: UserCreate, hashed_password: str) -> dict:
        return {
            "userId": user_id,
            "createdAt": datetime.now(timezone.utc),
            "username": data.username,
            "email": data.email,
            "role": data.role,
            "hashed_password": hashed_password,
        }

    # ----------------------
    # CRUD
    # ----------------------
    async def create(self, data: UserCreate, *, hashed_password: str) -> str:
        new_id = create_user_id()
        await self.col.insert_one(self._to_doc(new_id, data, hashed_password))
        return new_id

    async def get_by_id(self, user_id: str) -> Optional[User]:
        d = await self.col.find_one({"userId": str(user_id)})
        return self._from_doc(d) if d else None

    async def get_by_username(self, username: str) -> Optional[User]:
        d = await self.col.find_one({"username": username})
        return self._from_doc(d) if d else None

    async def get_by_email(self, email: str) -> Optional[User]:
        d = await self.col.find_one({"email": email})
        return self._from_doc(d) if d else None

    async def get_auth_by_email(self, email: str) -> Optional[Tuple[User, str]]:
        d = await self.col.find_one({"email": email})
        if not d:
            return None
        return self._from_doc(d), d["hashed_password"]

    async def delete_by_username(self, username: str) -> bool:
        res = await self.col.delete_one({"username": username})
        return res.deleted_count > 0

    # ----------------------
    # Indexes ("schema")
    # ----------------------
    async def ensure_indexes(self):
        # Unicità per username e email (se presenti)
        await self.col.create_index("username", unique=True, name="uq_users_username")
        await self.col.create_index("email", unique=True, sparse=True, name="uq_users_email")
        await self.col.create_index("userId", unique=True, name="uq_users_userId")