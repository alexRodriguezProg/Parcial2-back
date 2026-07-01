from typing import Optional, List
from sqlmodel import Session, select, func, or_
from app.repositories.base import BaseRepository
from app.models import Producto, Ingrediente, ProductoIngrediente, ProductoCategoria, UnidadMedida


class ProductoRepository(BaseRepository[Producto]):

    def __init__(self, session: Session):
        super().__init__(Producto, session)

    def get_available_stock(self, producto_id: int) -> int:
        """Calcula el stock máximo disponible de un producto basado en sus ingredientes.
        
        Retorna el mínimo entre (stock_ingrediente / cantidad_requerida) para cada ingrediente.
        Si no tiene ingredientes, retorna el stock_cantidad del producto.
        """
        producto = self.get_active_by_id(producto_id)
        if not producto:
            return 0
        
        ingredientes = self.session.exec(
            select(ProductoIngrediente, Ingrediente)
            .join(Ingrediente, ProductoIngrediente.ingrediente_id == Ingrediente.id)
            .where(ProductoIngrediente.producto_id == producto_id)
        ).all()
        
        if not ingredientes:
            return int(producto.stock_cantidad) if producto.stock_cantidad else 0
        
        max_stock = float('inf')
        for pi, ingrediente in ingredientes:
            if pi.cantidad and pi.cantidad > 0:
                stock_disponible = int(ingrediente.stock_cantidad // pi.cantidad)
                max_stock = min(max_stock, stock_disponible)
        
        return int(max_stock) if max_stock != float('inf') else 0

    def get_all_with_filters(self, skip=0, limit=20, categoria_id=None, disponible=None, search=None) -> tuple:
        """Devuelve productos con filtros opcionales y paginación."""
        statement = select(Producto).where(Producto.deleted_at == None)

        if categoria_id is not None:
            statement = (
                statement
                .join(ProductoCategoria, ProductoCategoria.producto_id == Producto.id)
                .where(ProductoCategoria.categoria_id == categoria_id)
            )
        if disponible is not None:
            statement = statement.where(Producto.disponible == disponible)
        if search:
            statement = statement.where(Producto.nombre.ilike(f"%{search}%"))

        total = self.session.exec(
            select(func.count()).select_from(statement.subquery())
        ).one()
        productos = self.session.exec(statement.offset(skip).limit(limit)).all()
        return productos, total

    def get_with_ingredientes(self, producto_id: int) -> Optional[Producto]:
        """Devuelve un producto con sus ingredientes y categorías."""
        producto = self.get_active_by_id(producto_id)
        if producto:
            _ = producto.productos_categoria
            _ = producto.productos_ingrediente
        return producto

    def add_ingrediente(self, producto_id: int, ingrediente_id: int, cantidad: float) -> None:
        """Asocia un ingrediente a un producto."""
        existing = self.session.exec(
            select(ProductoIngrediente).where(
                ProductoIngrediente.producto_id == producto_id,
                ProductoIngrediente.ingrediente_id == ingrediente_id,
            )
        ).first()
        if not existing:
            unidad = self.session.exec(select(UnidadMedida)).first()
            self.session.add(ProductoIngrediente(
                producto_id=producto_id,
                ingrediente_id=ingrediente_id,
                unidad_medida_id=unidad.id if unidad else 1,
                cantidad=cantidad,
                es_removible=False,
            ))
            self.session.flush()

    def remove_ingrediente(self, producto_id: int, ingrediente_id: int) -> None:
        """Desasocia un ingrediente de un producto."""
        existing = self.session.exec(
            select(ProductoIngrediente).where(
                ProductoIngrediente.producto_id == producto_id,
                ProductoIngrediente.ingrediente_id == ingrediente_id,
            )
        ).first()
        if existing:
            self.session.delete(existing)
            self.session.flush()

    def assign_categoria(self, producto_id: int, categoria_id: int, es_principal: bool = True) -> None:
        """Asocia una categoría a un producto."""
        existing = self.session.exec(
            select(ProductoCategoria).where(
                ProductoCategoria.producto_id == producto_id,
                ProductoCategoria.categoria_id == categoria_id,
            )
        ).first()
        if not existing:
            self.session.add(ProductoCategoria(
                producto_id=producto_id,
                categoria_id=categoria_id,
                es_principal=es_principal,
            ))
            self.session.flush()

    def remove_categoria(self, producto_id: int, categoria_id: int) -> None:
        """Desasocia una categoría de un producto."""
        existing = self.session.exec(
            select(ProductoCategoria).where(
                ProductoCategoria.producto_id == producto_id,
                ProductoCategoria.categoria_id == categoria_id,
            )
        ).first()
        if existing:
            self.session.delete(existing)
            self.session.flush()

    def get_productos_by_ingrediente(self, ingrediente_id: int) -> List[Producto]:
        """Devuelve todos los productos que usan un ingrediente específico."""
        statement = (
            select(Producto)
            .join(ProductoIngrediente, ProductoIngrediente.producto_id == Producto.id)
            .where(
                ProductoIngrediente.ingrediente_id == ingrediente_id,
                Producto.deleted_at == None,
            )
        )
        return list(self.session.exec(statement).all())


class IngredienteRepository(BaseRepository[Ingrediente]):

    def __init__(self, session: Session):
        super().__init__(Ingrediente, session)

    def get_all_with_filters(self, skip=0, limit=50, es_alergeno=None, search=None) -> tuple:
        """Devuelve ingredientes con filtros y paginación."""
        statement = select(Ingrediente).where(Ingrediente.deleted_at == None)
        if es_alergeno is not None:
            statement = statement.where(Ingrediente.es_alergeno == es_alergeno)
        if search:
            conditions = []
            try:
                conditions.append(Ingrediente.id == int(search))
            except ValueError:
                pass
            conditions.append(Ingrediente.nombre.ilike(f"%{search}%"))
            statement = statement.where(or_(*conditions))
        total = self.session.exec(
            select(func.count()).select_from(statement.subquery())
        ).one()
        items = self.session.exec(statement.offset(skip).limit(limit)).all()
        return items, total