from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Cookie, status 
from sqlmodel import Session
from app.core.database import get_session
from app.models import Usuario, RolCodigo
from app.repositories import UsuarioRepository
from app.core.security import decode_token

def get_current_user(
        access_token: Optional[str] = Cookie(default=None),
        session: Session = Depends(get_session),
) -> Usuario:
    if not access_token:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    
    payload = decode_token(access_token)
    usuario_id = int(payload.get("sub", 0))

    repo = UsuarioRepository(session)
    usuario = repo.get_with_roles(usuario_id)

    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    
    return usuario

CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> Usuario:
    user_roles = {r.codigo for r in current_user.roles}
    if RolCodigo.ADMIN not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol ADMIN")
    return current_user


def require_admin_or_stock(current_user: CurrentUser) -> Usuario:
    user_roles = {r.codigo for r in current_user.roles}
    if not {RolCodigo.ADMIN, RolCodigo.STOCK}.intersection(user_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol ADMIN o STOCK")
    return current_user


def require_admin_or_pedidos(current_user: CurrentUser) -> Usuario:
    user_roles = {r.codigo for r in current_user.roles}
    if not {RolCodigo.ADMIN, RolCodigo.PEDIDOS}.intersection(user_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol ADMIN o PEDIDOS")
    return current_user


AdminUser = Annotated[Usuario, Depends(require_admin)]
AdminOrStock = Annotated[Usuario, Depends(require_admin_or_stock)]
AdminOrPedidos = Annotated[Usuario, Depends(require_admin_or_pedidos)]