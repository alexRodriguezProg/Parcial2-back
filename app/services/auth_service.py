from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from fastapi import HTTPException, status
from app.core.config import settings
from app.models import Usuario, RolCodigo
from app.repositories import UsuarioRepository, UnitOfWork
from app.schemas.schemas import RegisterRequest, LoginRequest, UsuarioResponse, TokenResponse


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    data = payload.copy()
    data["exp"] = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


class AuthService:

    def register(self, data: RegisterRequest) -> tuple[dict, str]:
        with UnitOfWork() as uow:
            repo = UsuarioRepository(uow.session)
            if repo.get_by_email(data.email):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")
            usuario = Usuario(
                nombre=data.nombre, apellido=data.apellido,
                email=data.email, password_hash=hash_password(data.password),
                telefono=data.telefono,
            )
            usuario = repo.create(usuario)
            rol_client = repo.get_rol_by_codigo(RolCodigo.CLIENT)
            if rol_client:
                repo.assign_role(usuario.id, rol_client.id) # type: ignore
            uow.session.refresh(usuario)
            _ = usuario.roles
            token = create_access_token({"sub": str(usuario.id)})
            # Serializar dentro del UoW
            usuario_data = UsuarioResponse.model_validate(usuario).model_dump()
            return usuario_data, token

    def login(self, data: LoginRequest) -> tuple[dict, str]:
        with UnitOfWork() as uow:
            repo = UsuarioRepository(uow.session)
            usuario = repo.get_by_email(data.email)
            if not usuario or not verify_password(data.password, usuario.password_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
            if not usuario.activo:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
            _ = usuario.roles
            token = create_access_token({"sub": str(usuario.id)})
            # Serializar dentro del UoW
            usuario_data = UsuarioResponse.model_validate(usuario).model_dump()
            return usuario_data, token