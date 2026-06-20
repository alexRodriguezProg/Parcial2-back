from typing import Optional
from fastapi import HTTPException
from app.repositories import ProductoRepository, IngredienteRepository, UnitOfWork
from app.models import Producto, Ingrediente
from app.schemas.schemas import (
    ProductoCreate, ProductoUpdate, ProductoDisponibilidadUpdate,
    IngredienteCreate, IngredienteUpdate, AddIngredienteRequest,
    ProductoResponse, IngredienteResponse
)


class ProductoService:

    def get_all(self, skip=0, limit=20, categoria_id=None, disponible=None, search=None):
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            productos, total = repo.get_all_with_filters(
                skip=skip, limit=limit,
                categoria_id=categoria_id,
                disponible=disponible,
                search=search,
            )
            for p in productos:
                _ = p.productos_ingrediente
            items = [ProductoResponse.model_validate(p).model_dump() for p in productos]
            return total, items

    def get_by_id(self, producto_id: int):
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_with_ingredientes(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            return ProductoResponse.model_validate(p).model_dump()

    def create(self, data: ProductoCreate):
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
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def update(self, producto_id: int, data: ProductoUpdate):
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(p, key, value)
            uow.session.add(p)
            uow.session.flush()
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def update_disponibilidad(self, producto_id: int, data: ProductoDisponibilidadUpdate):
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            p.disponible = data.disponible
            if data.stock_cantidad is not None:
                p.stock_cantidad = data.stock_cantidad
            uow.session.add(p)
            uow.session.flush()
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()

    def update_imagenes(self, producto_id: int, imagenes_url: list[str]):
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
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            repo.soft_delete(p)

    def add_ingrediente(self, producto_id: int, data: AddIngredienteRequest):
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

    def remove_ingrediente(self, producto_id: int, ingrediente_id: int):
        with UnitOfWork() as uow:
            repo = ProductoRepository(uow.session)
            p = repo.get_active_by_id(producto_id)
            if not p:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            repo.remove_ingrediente(producto_id, ingrediente_id)
            uow.session.refresh(p)
            return ProductoResponse.model_validate(p).model_dump()


class IngredienteService:

    def get_all(self, skip=0, limit=50, es_alergeno=None, search=None):
        with UnitOfWork() as uow:
            items, total = IngredienteRepository(uow.session).get_all_with_filters(
                skip=skip, limit=limit, es_alergeno=es_alergeno, search=search
            )
            serialized = [IngredienteResponse.model_validate(i).model_dump() for i in items]
            return serialized, total

    def get_by_id(self, ingrediente_id: int):
        with UnitOfWork() as uow:
            ing = IngredienteRepository(uow.session).get_active_by_id(ingrediente_id)
            if not ing:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            return IngredienteResponse.model_validate(ing).model_dump()

    def create(self, data: IngredienteCreate):
        with UnitOfWork() as uow:
            repo = IngredienteRepository(uow.session)
            ing = repo.create(Ingrediente(
                nombre=data.nombre,
                descripcion=data.descripcion,
                es_alergeno=data.es_alergeno,
            ))
            uow.session.refresh(ing)
            return IngredienteResponse.model_validate(ing).model_dump()

    def update(self, ingrediente_id: int, data: IngredienteUpdate):
        with UnitOfWork() as uow:
            repo = IngredienteRepository(uow.session)
            ing = repo.get_active_by_id(ingrediente_id)
            if not ing:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(ing, key, value)
            uow.session.add(ing)
            uow.session.flush()
            uow.session.refresh(ing)
            return IngredienteResponse.model_validate(ing).model_dump()

    def delete(self, ingrediente_id: int) -> None:
        with UnitOfWork() as uow:
            repo = IngredienteRepository(uow.session)
            ing = repo.get_active_by_id(ingrediente_id)
            if not ing:
                raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
            repo.soft_delete(ing)