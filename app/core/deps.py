from fastapi import Request
from app.database.user_repo import UserRepo

def get_user_repository(request: Request) -> UserRepo:
    repo = getattr(request.app.state, "user_repo", None)
    if repo is None:
        raise RuntimeError("User repository non inizializzato")
    return repo
