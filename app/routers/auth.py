from fastapi import APIRouter, Response, status
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, UsuarioResponse
from app.services.auth_service import AuthService
from app.core.dependencies import CurrentUser, get_current_user
from app.core.config import settings
from fastapi import Depends
from sqlmodel import Session
from app.core.database import get_session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
service = AuthService()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, response: Response):
    usuario_data, token = service.register(data)
    response.set_cookie(key="access_token", value=token, httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="lax", secure=False)
    return {"access_token": token, "token_type": "bearer", "usuario": usuario_data}


@router.post("/login")
def login(data: LoginRequest, response: Response):
    usuario_data, token = service.login(data)
    response.set_cookie(key="access_token", value=token, httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite="lax", secure=False)
    return {"access_token": token, "token_type": "bearer", "usuario": usuario_data}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada"}


@router.get("/me")
def get_me(current_user: CurrentUser, session: Session = Depends(get_session)):
    from app.repositories import UsuarioRepository
    repo = UsuarioRepository(session)
    usuario = repo.get_with_roles(current_user.id) # type: ignore
    from app.schemas.schemas import UsuarioResponse
    return UsuarioResponse.model_validate(usuario).model_dump()