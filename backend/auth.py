"""
Authentication module: JWT-based role system.
Roles: 'engineer' (ask queries), 'admin' (upload manuals + ask queries)
Uses bcrypt directly (passlib is incompatible with bcrypt>=4.0).
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from tinydb import TinyDB, Query

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, DB_DIR

# ── OAuth2 scheme ─────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ── tiny persistent user store ────────────────────────────────────────────────
_user_db = TinyDB(DB_DIR / "users.json")
_UserQ = Query()


# ── Pydantic models ───────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserIn(BaseModel):
    username: str
    password: str
    role: str = "engineer"   # engineer | admin


class UserOut(BaseModel):
    username: str
    role: str


# ── helpers ───────────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_user(username: str) -> Optional[dict]:
    result = _user_db.search(_UserQ.username == username)
    return result[0] if result else None


def create_user(username: str, password: str, role: str = "engineer") -> UserOut:
    if get_user(username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if role not in ("engineer", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'engineer' or 'admin'")
    _user_db.insert({"username": username, "hashed_password": _hash(password), "role": role})
    return UserOut(username=username, role=role)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user or not _verify(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── FastAPI dependencies ──────────────────────────────────────────────────────
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_engineer(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in ("engineer", "admin"):
        raise HTTPException(status_code=403, detail="Engineer or Admin access required")
    return current_user


# ── Seed default accounts if DB is empty ─────────────────────────────────────
def seed_defaults():
    if not _user_db.all():
        create_user("admin", "admin123", "admin")
        create_user("engineer", "eng123", "engineer")
        print("[Auth] Seeded default users: admin/admin123, engineer/eng123")
