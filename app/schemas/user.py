# app/schemas/user.py
from pydantic import BaseModel
from typing import Optional

# Per la registrazione di un nuovo utente
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str  # "teacher", "student", "admin"

# Per il login
class UserLogin(BaseModel):
    email: str
    password: str

# Per rispondere al client con dati pubblici dell'utente
class User(BaseModel):
    userId: str
    username: str
    email: Optional[str] = None
    role: str

# Per il token JWT
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[int] = None
    issued_at: Optional[int] = None
