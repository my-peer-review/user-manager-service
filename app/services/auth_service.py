# app/services/auth_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple, Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.deps import get_user_repository
from app.database.user_repo import UserRepo
from app.schemas.user import User
from app.services.user_service import UserService


UserRepoDep = Annotated[UserRepo, Depends(get_user_repository)]
_security = HTTPBearer(auto_error=True)


class AuthService:

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)


    @staticmethod
    def create_access_token(
        claims: Dict[str, Any],
        *,
        expires_in_seconds: int = 3600,
    ) -> Tuple[str, int, int]:
        """
        Ritorna (token, exp_ts, iat_ts) con payload:
        { sub, role, iat, exp }
        """
        if "sub" not in claims or "role" not in claims:
            raise ValueError("claims must include 'sub' and 'role'")

        now = AuthService._now()
        iat_ts = int(now.timestamp())
        exp_ts = int((now + timedelta(seconds=expires_in_seconds)).timestamp())

        payload = {**claims, "iat": iat_ts, "exp": exp_ts}
        try:
            token = jwt.encode(
                payload,
                settings.jwt_private_key,
                algorithm=settings.jwt_algorithm,
            )
        except Exception as e:
            raise RuntimeError(f"JWT encode error: {e}") from e

        return token, exp_ts, iat_ts


    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                settings.jwt_public_key,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


    @staticmethod
    async def current_user(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> User:

        payload = AuthService.decode_token(credentials.credentials)
        sub = payload.get("sub")
        role = payload.get("role")
        if not sub or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        User = UserService.get_user_by_id(sub, repo=Depends(UserRepo))

        if not User:
            raise HTTPException(status_code=404, detail="User not found")

        # Non abbiamo l'ID numerico nel token: lo lasciamo a -1 (come placeholder).
        # Se vuoi l'ID reale, nel router /me puoi caricarlo dal DB usando lo username (sub).
        return User

# --- piccolo helper opzionale (evita whitespace strani) ---
def substr(s: str) -> str:
    return s.strip()
