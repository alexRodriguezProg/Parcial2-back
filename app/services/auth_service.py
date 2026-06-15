from fastapi import HTTPException, status
from app.models import Usuario, RolCodigo
from app.repositories import UsuarioRepository, UnitOfWork
from app.schemas.schemas import RegisterRequest, LoginRequest, UsuarioResponse
from app.core.security import hash_password, verify_password, create_access_token


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
                repo.assign_role(usuario.id, rol_client.id)  # type: ignore
            uow.session.refresh(usuario)
            _ = usuario.roles
            token = create_access_token({"sub": str(usuario.id)})
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
            usuario_data = UsuarioResponse.model_validate(usuario).model_dump()
            return usuario_data, token