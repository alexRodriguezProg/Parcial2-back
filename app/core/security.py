from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT con payload y expiración."""
    data = payload.copy()
    data["exp"] = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza 401 si expiró o es inválido."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")