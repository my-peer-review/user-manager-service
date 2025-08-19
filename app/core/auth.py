# app/core/auth.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.schemas.context import UserContext

# === Config ===
JWT_ALGORITHM = settings.jwt_algorithm
PRIVATE_KEY = settings.jwt_private_key
PUBLIC_KEY = settings.jwt_public_key

# Estrai il Bearer token dall'header Authorization
security = HTTPBearer(auto_error=True)

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def create_access_token(
    claims: Dict[str, Any],
    *,
    expires_in_seconds: int = 3600,
) -> Tuple[str, int, int]:
    """
    Crea un JWT firmato con:
      - sub, role (provenienti da `claims`)
      - iat (epoch seconds)
      - exp (epoch seconds)

    Ritorna: (token_str, exp_ts, iat_ts)
    """
    if "sub" not in claims or "role" not in claims:
        raise ValueError("claims must include 'sub' and 'role'")

    now = _utcnow()
    iat_ts = int(now.timestamp())
    exp_ts = int((now + timedelta(seconds=expires_in_seconds)).timestamp())

    payload = {
        **claims,
        "iat": iat_ts,
        "exp": exp_ts,
    }

    try:
        token = jwt.encode(payload, PRIVATE_KEY, algorithm=JWT_ALGORITHM)
    except Exception as e:
        # Tipicamente errori di chiave/algoritmo non validi
        raise RuntimeError(f"JWT encode error: {e}") from e

    return token, exp_ts, iat_ts


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica e valida un JWT (firma + exp).
    Ritorna il payload.
    """
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserContext:
    """
    Dependency FastAPI:
    - legge il Bearer token
    - decodifica/valida
    - costruisce e ritorna UserContext
    """
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return UserContext(user_id=user_id, role=role)
