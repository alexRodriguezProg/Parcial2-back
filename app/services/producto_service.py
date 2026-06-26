from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.repositories import ProductoRepository, IngredienteRepository, CategoriaRepository, UnitOfWork
from app.models import Producto, Ingrediente
from app.schemas.schemas import (
    ProductoCreate, ProductoUpdate, ProductoDisponibilidadUpdate,
    IngredienteCreate, IngredienteUpdate, AddIngredienteRequest,
    AddCategoriaRequest,
    ProductoResponse, IngredienteResponse
)


class ProductoService:

    def get_all(self, skip=0, limit=20, categoria_id=None, disponible=None, search=None) -> tuple:
        """Devuelve productos con filtros opcionales."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            productos, total = repo.get_all_with_filters(
                skip=skip, limit=limit,
                categoria_id=categoria_id,
                disponible=disponible,
                search=search,
            )
            for p in productos:
                _ = p.productos_categoria
                _ = p.productos_ingrediente
            items = [ProductoResponse.model_validate(p).model_dump() for p in productos]
            return total, items

    def get_by_id(self, producto_id: int) -> dict:
        """Devuelve un producto con ingredientes y categorías."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_with_ingredientes(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            return ProductoResponse.model_validate(p).model_dump()

    def create(self, data: ProductoCreate) -> dict:
        """Crea un producto nuevo con categorías e ingredientes."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.create(Producto(
                nombre=data.nombre,
                descripcion=data.descripcion,
                precio_base=data.precio_base,
                imagenes_url=data.imagenes_url,
                stock_cantidad=data.stock_cantidad,
                disponible=data.disponible,
                unidad_venta_id=data.unidad_venta_id,
            ))
            uow.session.flush()

            if data.categoria_ids:
                cat_repo = CategoriaRepository(uow.session)
                for cat_id in data.categoria_ids:
                    if cat_repo.get_active_by_id(cat_id):
                        repo.assign_categoria(p.id, cat_id, True)

            if data.ingredientes:
                for ing in data.ingredientes:
                    repo.add_ingrediente(p.id, ing.ingrediente_id, ing.cantidad)

            uow.session.refresh(p)
            _ = p.productos_categoria
            _ = p.productos_ingrediente
            return ProductoResponse.model_validate(p).model_dump()

    def update(self, producto_id: int, data: ProductoUpdate) -> dict:
        """Actualiza un producto existente."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(p, key, value)
            # Auto‑sync: si se actualiza stock, recalcular disponible siempre
            if "stock_cantidad" in update_data:
                p.disponible = p.stock_cantidad > 0
            uow.session.add(p)
            uow.session.flush()
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def update_disponibilidad(self, producto_id: int, data: ProductoDisponibilidadUpdate) -> dict:
        """Actualiza disponibilidad y stock de un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            p.disponible = data.disponible
            if data.stock_cantidad is not None:
                p.stock_cantidad = data.stock_cantidad
            # No permitir activar un producto con stock 0
            if p.stock_cantidad <= 0:
                p.disponible = False
            uow.session.add(p)
            uow.session.flush()
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def update_imagenes(self, producto_id: int, imagenes_url: list[str]) -> dict:
        """Actualiza las imágenes de un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            p.imagenes_url = imagenes_url
            uow.session.add(p)
            uow.session.flush()
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def delete(self, producto_id: int) -> None:
        """Elimina (soft delete) un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            repo.soft_delete(p)

    def add_ingrediente(self, producto_id: int, data: AddIngredienteRequest) -> dict:
        """Agrega un ingrediente a un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            ing_repo = IngredienteRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            if not ing_repo.get_active_by_id(data.ingrediente_id):
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            repo.add_ingrediente(producto_id, data.ingrediente_id, data.cantidad)
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def remove_ingrediente(self, producto_id: int, ingrediente_id: int) -> dict:
        """Saca un ingrediente de un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            repo.remove_ingrediente(producto_id, ingrediente_id)
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def assign_categoria(self, producto_id: int, data: AddCategoriaRequest) -> dict:
        """Asigna una categoría a un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            cat_repo = CategoriaRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            if not cat_repo.get_active_by_id(data.categoria_id):
                raise HTTPException(status_code=404, detail="Categoria no encontrada")
            repo.assign_categoria(producto_id, data.categoria_id, data.es_principal)
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def remove_categoria(self, producto_id: int, categoria_id: int) -> dict:
        """Saca una categoría de un producto."""
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            repo.remove_categoria(producto_id, categoria_id)
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()


class IngredienteService:

    def get_all(self, skip=0, limit=50, es_alergeno=None, search=None) -> tuple:
        """Devuelve ingredientes con filtros opcionales."""
        with UnitOfWork() as uow:
            items, total = IngredienteRepository(uow.session).get_all_with_filters(
                skip=skip, limit=limit, es_alergeno=es_alergeno, search=search
            )
            serialized = [IngredienteResponse.model_validate(i).model_dump() for i in items]
            return serialized, total

    def get_by_id(self, ingrediente_id: int) -> dict:
        """Devuelve un ingrediente por ID."""
        with UnitOfWork() as uow:
            ing = IngredienteRepository(uow.session).get_active_by_id(ingrediente_id)
            if not ing:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            return IngredienteResponse.model_validate(ing).model_dump()

    def create(self, data: IngredienteCreate) -> dict:
        """Crea un ingrediente nuevo."""
        with UnitOfWork() as uow:
            repo = IngredienteRepository(uow.session)
            try:
                ing = repo.create(Ingrediente(
                    nombre=data.nombre,
                    descripcion=data.descripcion,
                    es_alergeno=data.es_alergeno,
                ))
                uow.session.refresh(ing)
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un ingrediente con ese nombre."
                )
            return IngredienteResponse.model_validate(ing).model_dump()

    def update(self, ingrediente_id: int, data: IngredienteUpdate) -> dict:
        """Actualiza un ingrediente existente."""
        with UnitOfWork() as uow:
            repo = IngredienteRepository(uow.session)
            ing = repo.get_active_by_id(ingrediente_id)
            if not ing:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(ing, key, value)
            uow.session.add(ing)
            try:
                uow.session.flush()
                uow.session.refresh(ing)
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un ingrediente con ese nombre."
                )
            return IngredienteResponse.model_validate(ing).model_dump()

    def delete(self, ingrediente_id: int) -> None:
        """Elimina (soft delete) un ingrediente."""
        with UnitOfWork() as uow:
            repo = IngredienteRepository(uow.session)
            ing = repo.get_active_by_id(ingrediente_id)
            if not ing:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            repo.soft_delete(ing)