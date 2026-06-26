from fastapi import APIRouter, Response, Request, Depends, status
from sqlmodel import Session
from app.schemas.schemas import RegisterRequest, LoginRequest, UsuarioResponse
from app.services.auth_service import AuthService
from app.core.dependencies import CurrentUser
from app.core.database import get_session
from app.core.config import settings
from app.core.rate_limit import (
    verificar_rate_limit,
    registrar_intento_fallido,
    limpiar_intentos,
)

router  = APIRouter(prefix="/api/v1/auth", tags=["auth"])
service = AuthService()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, response: Response, request: Request):
    """POST /auth/register — Registra un nuevo usuario."""
    verificar_rate_limit(request)
    try:
        usuario_data, token = service.register(data)
    except Exception:
        registrar_intento_fallido(request)
        raise
    limpiar_intentos(request)
    response.set_cookie(
        key="access_token", value=token, httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax", secure=False,
    )
    return {"access_token": token, "token_type": "bearer", "usuario": usuario_data}


@router.post("/login")
def login(data: LoginRequest, response: Response, request: Request):
    """POST /auth/login — Autentica un usuario existente."""
    verificar_rate_limit(request)
    try:
        usuario_data, token = service.login(data)
    except Exception:
        registrar_intento_fallido(request)
        raise
    limpiar_intentos(request)
    response.set_cookie(
        key="access_token", value=token, httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax", secure=False,
    )
    return {"access_token": token, "token_type": "bearer", "usuario": usuario_data}


@router.post("/logout")
def logout(response: Response):
    """POST /auth/logout — Cierra la sesión del usuario."""
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada"}


@router.get("/me")
def get_me(current_user: CurrentUser, session: Session = Depends(get_session)):
    """GET /auth/me — Devuelve los datos del usuario autenticado."""
    from app.repositories import UsuarioRepository
    repo    = UsuarioRepository(session)
    usuario = repo.get_with_roles(current_user.id)  # type: ignore
    return UsuarioResponse.model_validate(usuario).model_dump()