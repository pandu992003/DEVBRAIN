"""
Security utilities: JWT + password hashing.
Uses bcrypt directly (passlib is incompatible with bcrypt>=4.0).
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    print(f"   [Debug Token] Decoding token: {token[:15]}...")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"   [Debug Token] Payload: {payload}")
        return payload
    except JWTError as e:
        print(f"   [Debug Token] JWTError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    print(f"   [Debug User] get_current_user started. Token length: {len(token)}")
    from app.services.user_service import get_user_by_id
    payload = decode_token(token)
    user_id: str | None = payload.get("sub")
    if not user_id:
        print("   [Debug User] Missing 'sub' in payload")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    print(f"   [Debug User] User ID extracted: {user_id}")
    user = await get_user_by_id(db, int(user_id))
    if not user:
        print("   [Debug User] User not found in DB")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    print(f"   [Debug User] Success. User: {user.email}")
    return user
