# app/database/user_repo.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from app.schemas.user import UserCreate, User


class UserRepo(ABC):
    """Repository pattern per gli utenti (astrazione DB)."""

    @abstractmethod
    async def create(self, data: UserCreate, *, hashed_password: str) -> int:
        """
        Crea un utente e ritorna l'ID generato.
        NOTA: il service si occupa di hashare la password e passare `hashed_password`.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Ritorna l'utente per ID, oppure None se non esiste."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Ritorna l'utente per username, oppure None."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Ritorna l'utente per email, oppure None."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_auth_by_email(self, email: str) -> Optional[Tuple[User, str]]:
        """Ritorna (User, hashed_password) per email, oppure None."""
        raise NotImplementedError
