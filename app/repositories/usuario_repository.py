from typing import Optional, List
from sqlmodel import Session, select, func
from app.repositories.base import BaseRepository
from app.models import Usuario, Rol, UsuarioRol, RolCodigo


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        super().__init__(Usuario, session)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Devuelve un usuario activo por email."""
        return self.session.exec(
            select(Usuario).where(Usuario.email == email, Usuario.deleted_at == None)
        ).first()

    def get_with_roles(self, usuario_id: int) -> Optional[Usuario]:
        """Devuelve un usuario con sus roles cargados."""
        usuario = self.session.get(Usuario, usuario_id)
        if usuario and usuario.deleted_at is None:
            _ = usuario.roles
            return usuario
        return None

    def get_all_paginated(self, skip=0, limit=20, rol_codigo=None) -> tuple:
        """Devuelve usuarios con paginación y filtro opcional por rol."""
        statement = select(Usuario).where(Usuario.deleted_at == None)
        if rol_codigo:
            statement = (
                statement
                .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
                .where(UsuarioRol.rol_codigo == rol_codigo)
            )
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        usuarios = self.session.exec(statement.offset(skip).limit(limit)).all()
        return usuarios, total

    def assign_role(self, usuario_id: int, rol_codigo: RolCodigo) -> None:
        """Asigna un rol a un usuario."""
        existing = self.session.exec(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.rol_codigo == rol_codigo,
            )
        ).first()
        if not existing:
            self.session.add(UsuarioRol(usuario_id=usuario_id, rol_codigo=rol_codigo))
            self.session.flush()

    def remove_role(self, usuario_id: int, rol_codigo: RolCodigo) -> None:
        """Saca un rol a un usuario."""
        existing = self.session.exec(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.rol_codigo == rol_codigo,
            )
        ).first()
        if existing:
            self.session.delete(existing)
            self.session.flush()

    def get_roles(self) -> List[Rol]:
        """Devuelve todos los roles disponibles."""
        return self.session.exec(select(Rol)).all()

    def get_rol_by_codigo(self, codigo: RolCodigo) -> Optional[Rol]:
        """Devuelve un rol por su código."""
        return self.session.exec(select(Rol).where(Rol.codigo == codigo)).first()