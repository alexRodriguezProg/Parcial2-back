from typing import Annotated, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.schemas import UsuarioResponse, UsuarioUpdateRequest, AsignarRolRequest
from app.core.dependencies import AdminUser
from app.repositories import UsuarioRepository, UnitOfWork
from app.models import RolCodigo

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/usuarios", response_model=dict)
def list_usuarios(_: AdminUser, skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20, rol_codigo: Annotated[Optional[str], Query()] = None):
    with UnitOfWork() as uow:
        repo = UsuarioRepository(uow.session)
        usuarios, total = repo.get_all_paginated(skip=skip, limit=limit, rol_codigo=rol_codigo)
        for u in usuarios: _ = u.roles # type: ignore
        return {"total": total, "skip": skip, "limit": limit, "items": [UsuarioResponse.model_validate(u).model_dump() for u in usuarios]}


@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, _: AdminUser):
    with UnitOfWork() as uow:
        usuario = UsuarioRepository(uow.session).get_with_roles(usuario_id)
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UsuarioResponse.model_validate(usuario)


@router.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(usuario_id: int, data: UsuarioUpdateRequest, _: AdminUser):
    with UnitOfWork() as uow:
        repo = UsuarioRepository(uow.session)
        usuario = repo.get_with_roles(usuario_id)
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        usuario = repo.update(usuario, data.model_dump(exclude_unset=True))
        _ = usuario.roles # type: ignore
        return UsuarioResponse.model_validate(usuario)


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id: int, _: AdminUser):
    with UnitOfWork() as uow:
        repo = UsuarioRepository(uow.session)
        usuario = repo.get_active_by_id(usuario_id)
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        repo.soft_delete(usuario)


@router.post("/usuarios/{usuario_id}/roles", response_model=UsuarioResponse)
def asignar_rol(usuario_id: int, data: AsignarRolRequest, _: AdminUser):
    with UnitOfWork() as uow:
        repo = UsuarioRepository(uow.session)
        usuario = repo.get_with_roles(usuario_id)
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        rol = repo.get_rol_by_codigo(data.rol_codigo)
        if not rol: raise HTTPException(status_code=404, detail="Rol no encontrado")
        repo.assign_role(usuario_id, rol.id) # type: ignore
        uow.session.refresh(usuario)
        _ = usuario.roles # type: ignore
        return UsuarioResponse.model_validate(usuario)


@router.delete("/usuarios/{usuario_id}/roles/{rol_codigo}", response_model=UsuarioResponse)
def remover_rol(usuario_id: int, rol_codigo: RolCodigo, _: AdminUser):
    with UnitOfWork() as uow:
        repo = UsuarioRepository(uow.session)
        usuario = repo.get_with_roles(usuario_id)
        if not usuario: raise HTTPException(status_code=404, detail="Usuario no encontrado")
        rol = repo.get_rol_by_codigo(rol_codigo)
        if not rol: raise HTTPException(status_code=404, detail="Rol no encontrado")
        repo.remove_role(usuario_id, rol.id) # type: ignore
        uow.session.refresh(usuario)
        _ = usuario.roles # type: ignore
        return UsuarioResponse.model_validate(usuario)


@router.get("/roles")
def list_roles(_: AdminUser):
    with UnitOfWork() as uow:
        roles = UsuarioRepository(uow.session).get_roles()
        return [{"id": r.id, "nombre": r.nombre, "codigo": r.codigo} for r in roles]