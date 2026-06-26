from typing import Optional, List
from sqlmodel import Session, select
from app.repositories.base import BaseRepository
from app.models import Categoria, ProductoCategoria


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session: Session):
        super().__init__(Categoria, session)

    def get_all_with_filter(self, parent_id=None, include_subcategorias=False, skip=0, limit=100) -> tuple:
        """Devuelve categorías con filtro de padre y subcategorías."""
        statement = select(Categoria).where(Categoria.deleted_at == None)
        if parent_id is not None:
            statement = statement.where(Categoria.parent_id == parent_id)
        elif not include_subcategorias:
            statement = statement.where(Categoria.parent_id == None)
        from sqlmodel import func
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        categorias = self.session.exec(statement.offset(skip).limit(limit)).all()
        return categorias, total

    def get_subcategorias(self, parent_id: int) -> List[Categoria]:
        """Devuelve las subcategorías activas de una categoría."""
        return self.session.exec(
            select(Categoria).where(Categoria.parent_id == parent_id, Categoria.deleted_at == None)
        ).all()

    def has_active_productos(self, categoria_id: int) -> bool:
        """Verifica si una categoría tiene productos asociados."""
        return self.session.exec(
            select(ProductoCategoria).where(ProductoCategoria.categoria_id == categoria_id)
        ).first() is not None

    def get_all_flat(self, search=None) -> List[Categoria]:
        """Devuelve todas las categorías activas en lista plana, con búsqueda opcional."""
        statement = select(Categoria).where(Categoria.deleted_at == None)
        if search:
            from sqlmodel import or_
            conditions = []
            try:
                conditions.append(Categoria.id == int(search))
            except ValueError:
                pass
            conditions.append(Categoria.nombre.ilike(f"%{search}%"))
            statement = statement.where(or_(*conditions))
        return self.session.exec(statement).all()