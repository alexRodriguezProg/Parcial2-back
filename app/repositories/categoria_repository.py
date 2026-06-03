from typing import Optional, List
from sqlmodel import Session, select
from app.repositories.base import BaseRepository
from app.models import Categoria, Producto


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session: Session):
        super().__init__(Categoria, session)

    def get_all_with_filter(self, parent_id=None, include_subcategorias=False, skip=0, limit=100):
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
        return self.session.exec(
            select(Categoria).where(Categoria.parent_id == parent_id, Categoria.deleted_at == None)
        ).all()

    def has_active_productos(self, categoria_id: int) -> bool:
        return self.session.exec(
            select(Producto).where(Producto.categoria_id == categoria_id, Producto.deleted_at == None)
        ).first() is not None

    def get_all_flat(self) -> List[Categoria]:
        return self.session.exec(select(Categoria).where(Categoria.deleted_at == None)).all()