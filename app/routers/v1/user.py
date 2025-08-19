# app/routers/v1/user.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse

from app.schemas.user import UserCreate, UserLogin, User, Token
from app.core.deps import get_user_repository
from app.database.user_repo import UserRepo
from app.services.user_service import UserService
from app.services.auth_service import AuthService

router = APIRouter()

# DI solo per il repo (come richiesto)
UserRepoDep = Annotated[UserRepo, Depends(get_user_repository)]

@router.post("/user/register", status_code=status.HTTP_201_CREATED)
async def register_endpoint(payload: UserCreate, repo: UserRepoDep):
    try:
        new_user_id = await UserService.register(payload, repo)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "User created successfully.", "user_id": new_user_id}
        )
    except ValueError as e:
        # Utente già esistente -> 409
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/user/login", response_model=Token)
async def login_endpoint(credentials: UserLogin, repo: UserRepoDep):
    user = await UserService.authenticate(credentials, repo)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token, exp_ts, iat_ts = AuthService.create_access_token(
        {"sub": user.username, "role": user.role}
    )
    return Token(
        access_token=token,
        token_type="bearer",
        expires_at=exp_ts,
        issued_at=iat_ts,
    )
    
# ADMIN 

@router.delete("/user/{username}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    username: str,
    repo: UserRepoDep,
    current_user: User = Depends(AuthService.current_user),
):
    # Solo admin o lo stesso utente possono cancellare
    if current_user.role != "admin" and current_user.username != username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    deleted = await repo.delete_by_username(username)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.get("/user/me", response_model=User)
async def me_endpoint(current_user: User = Depends(AuthService.current_user)):
    # Nessun alias CurrentUserDep: la dependency è inline.
    return current_user
