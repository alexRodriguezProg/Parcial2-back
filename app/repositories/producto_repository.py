from typing import Optional, List
from sqlmodel import Session, select
from app.repositories.base import BaseRepository
from app.models import Producto, Ingrediente, ProductoIngrediente


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session: Session):
        super().__init__(Producto, session)

    def get_all_with_filters(self, skip=0, limit=20, categoria_id=None, disponible=None, search=None):
        statement = select(Producto).where(Producto.deleted_at == None)
        if categoria_id is not None:
            statement = statement.where(Producto.categoria_id == categoria_id)
        if disponible is not None:
            statement = statement.where(Producto.disponible == disponible)
        if search:
            statement = statement.where(Producto.nombre.ilike(f"%{search}%"))
        from sqlmodel import func
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        productos = self.session.exec(statement.offset(skip).limit(limit)).all()
        return productos, total

    def get_with_ingredientes(self, producto_id: int) -> Optional[Producto]:
        producto = self.get_active_by_id(producto_id)
        if producto:
            _ = producto.ingredientes
        return producto

    def add_ingrediente(self, producto_id: int, ingrediente_id: int, cantidad=None):
        existing = self.session.exec(
            select(ProductoIngrediente).where(
                ProductoIngrediente.producto_id == producto_id,
                ProductoIngrediente.ingrediente_id == ingrediente_id
            )
        ).first()
        if not existing:
            self.session.add(ProductoIngrediente(producto_id=producto_id, ingrediente_id=ingrediente_id, cantidad=cantidad))
            self.session.flush()

    def remove_ingrediente(self, producto_id: int, ingrediente_id: int):
        existing = self.session.exec(
            select(ProductoIngrediente).where(
                ProductoIngrediente.producto_id == producto_id,
                ProductoIngrediente.ingrediente_id == ingrediente_id
            )
        ).first()
        if existing:
            self.session.delete(existing)
            self.session.flush()


class IngredienteRepository(BaseRepository[Ingrediente]):
    def __init__(self, session: Session):
        super().__init__(Ingrediente, session)

    def get_all_with_filters(self, skip=0, limit=50, es_alergeno=None, search=None):
        statement = select(Ingrediente).where(Ingrediente.deleted_at == None)
        if es_alergeno is not None:
            statement = statement.where(Ingrediente.es_alergeno == es_alergeno)
        if search:
            statement = statement.where(Ingrediente.nombre.ilike(f"%{search}%"))
        from sqlmodel import func
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(statement.offset(skip).limit(limit)).all()
        return items, total