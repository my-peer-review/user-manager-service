# app/services/user_service.py
from __future__ import annotations

from typing import Optional, Tuple
import bcrypt

from app.schemas.user import UserCreate, UserLogin, User
from app.database.user_repo import UserRepo


# --- helpers pw ---
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


class UserService:
    """
    Service "semplice":
    - register(...) -> int (ID utente creato)
    - authenticate(...) -> Optional[User]
    Note:
      * non introduce UserInDB
      * per l'autenticazione il repo fornisce (User, hashed_password)
    """

    # -------------------------------
    #           REGISTER
    # -------------------------------
    async def register(data: UserCreate, repo: UserRepo) -> int:
        username = data.username.strip()
        email = data.email.strip().lower() if data.email else None
        normalized = UserCreate(
            username=username, password=data.password, email=email, role=data.role
        )

        # Pre-check di univocità (best effort; il vincolo reale è a DB)
        if email and await repo.get_by_email(email):
            raise ValueError("Email already exists")

        # Persist
        hashed = _hash_password(data.password)
        try:
            new_id = await repo.create(normalized, hashed_password=hashed)
            return new_id
        except Exception as e:
            # Copre le race condition: se due richieste simultanee passano il pre-check,
            # il DB lancerà vincolo UNIQUE. Mappiamo a 409.
            raise ValueError("User already exists") from e

    # -------------------------------
    #          AUTHENTICATE
    # -------------------------------
    async def authenticate(credentials: UserLogin, repo: UserRepo) -> Optional[User]:
        """
        Ritorna User se credenziali valide, altrimenti None.
        Repository necessario:
          - get_auth_by_username(username) -> Optional[tuple[User, hashed_password]]
          - get_auth_by_email(email) -> Optional[tuple[User, hashed_password]]
        """
        identifier = credentials.email.strip()

        record: Optional[Tuple[User, str]] = None

        if identifier:
            record = await repo.get_auth_by_email(identifier)

        if not record:
            return None

        user, hashed = record
        if not _verify_password(credentials.password, hashed):
            return None

        return user
