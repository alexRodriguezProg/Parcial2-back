from typing import Annotated, Optional
from fastapi import APIRouter, Query, status
from pydantic import BaseModel
from sqlmodel import select, Session
from app.schemas.schemas import (
    ProductoCreate, ProductoUpdate, ProductoDisponibilidadUpdate, ProductoResponse,
    IngredienteCreate, IngredienteUpdate, IngredienteResponse, AddIngredienteRequest,
    AddCategoriaRequest, UnidadMedidaResponse,
)
from app.models import UnidadMedida
from app.core.database import engine

class ImagenesUpdate(BaseModel):
    imagenes_url: list[str]
from app.services.producto_service import ProductoService, IngredienteService
from app.core.dependencies import AdminUser, AdminOrStock

ingredientes_router = APIRouter(prefix="/api/v1/ingredientes", tags=["ingredientes"])
productos_router = APIRouter(prefix="/api/v1/productos", tags=["productos"])
unidades_router = APIRouter(prefix="/api/v1/unidades-medida", tags=["unidades-medida"])

producto_service = ProductoService()
ingrediente_service = IngredienteService()


@ingredientes_router.get("/", response_model=dict)
def list_ingredientes(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    es_alergeno: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
):
    """GET /ingredientes — Lista ingredientes con filtros."""
    items, total = ingrediente_service.get_all(skip=skip, limit=limit, es_alergeno=es_alergeno, search=search)
    return {"total": total, "skip": skip, "limit": limit, "items": [IngredienteResponse.model_validate(i).model_dump() for i in items]}


@ingredientes_router.get("/{ingrediente_id}", response_model=IngredienteResponse)
def get_ingrediente(ingrediente_id: int):
    """GET /ingredientes/{id} — Obtiene un ingrediente por ID."""
    return ingrediente_service.get_by_id(ingrediente_id)


@ingredientes_router.post("/", response_model=IngredienteResponse, status_code=status.HTTP_201_CREATED)
def create_ingrediente(data: IngredienteCreate, _: AdminUser):
    """POST /ingredientes — Crea un nuevo ingrediente."""
    return ingrediente_service.create(data)


@ingredientes_router.put("/{ingrediente_id}", response_model=IngredienteResponse)
def update_ingrediente(ingrediente_id: int, data: IngredienteUpdate, _: AdminUser):
    """PUT /ingredientes/{id} — Actualiza un ingrediente existente."""
    return ingrediente_service.update(ingrediente_id, data)


@ingredientes_router.delete("/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingrediente(ingrediente_id: int, _: AdminUser):
    """DELETE /ingredientes/{id} — Elimina un ingrediente."""
    ingrediente_service.delete(ingrediente_id)


@productos_router.get("/", response_model=dict)
def list_productos(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    categoria_id: Annotated[Optional[int], Query()] = None,
    disponible: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
):
    """GET /productos — Lista productos con filtros."""
    total, items = producto_service.get_all(skip=skip, limit=limit, categoria_id=categoria_id, disponible=disponible, search=search)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@productos_router.get("/{producto_id}", response_model=ProductoResponse)
def get_producto(producto_id: int):
    """GET /productos/{id} — Obtiene un producto por ID."""
    return producto_service.get_by_id(producto_id)


@productos_router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(data: ProductoCreate, _: AdminUser):
    """POST /productos — Crea un nuevo producto."""
    return producto_service.create(data)


@productos_router.put("/{producto_id}", response_model=ProductoResponse)
def update_producto(producto_id: int, data: ProductoUpdate, _: AdminUser):
    """PUT /productos/{id} — Actualiza un producto existente."""
    return producto_service.update(producto_id, data)


@productos_router.patch("/{producto_id}/disponibilidad", response_model=ProductoResponse)
def update_disponibilidad(producto_id: int, data: ProductoDisponibilidadUpdate, _: AdminOrStock):
    """PATCH /productos/{id}/disponibilidad — Cambia la disponibilidad de un producto."""
    return producto_service.update_disponibilidad(producto_id, data)


@productos_router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(producto_id: int, _: AdminUser):
    """DELETE /productos/{id} — Elimina un producto."""
    producto_service.delete(producto_id)


@productos_router.patch("/{producto_id}/imagenes", response_model=ProductoResponse)
def update_producto_imagenes(producto_id: int, data: ImagenesUpdate, _: AdminUser):
    """PATCH /productos/{id}/imagenes — Actualiza las imágenes de un producto."""
    return producto_service.update_imagenes(producto_id, data.imagenes_url)


@productos_router.post("/{producto_id}/ingredientes", response_model=ProductoResponse)
def add_ingrediente(producto_id: int, data: AddIngredienteRequest, _: AdminUser):
    """POST /productos/{id}/ingredientes — Agrega un ingrediente a un producto."""
    return producto_service.add_ingrediente(producto_id, data)


@productos_router.delete("/{producto_id}/ingredientes/{ingrediente_id}", response_model=ProductoResponse)
def remove_ingrediente(producto_id: int, ingrediente_id: int, _: AdminUser):
    """DELETE /productos/{id}/ingredientes/{id} — Remueve un ingrediente de un producto."""
    return producto_service.remove_ingrediente(producto_id, ingrediente_id)


@productos_router.post("/{producto_id}/categorias", response_model=ProductoResponse)
def assign_categoria(producto_id: int, data: AddCategoriaRequest, _: AdminUser):
    """POST /productos/{id}/categorias — Asigna una categoría a un producto."""
    return producto_service.assign_categoria(producto_id, data)


@productos_router.delete("/{producto_id}/categorias/{categoria_id}", response_model=ProductoResponse)
def remove_categoria(producto_id: int, categoria_id: int, _: AdminUser):
    """DELETE /productos/{id}/categorias/{id} — Remueve una categoría de un producto."""
    return producto_service.remove_categoria(producto_id, categoria_id)


@productos_router.get("/{producto_id}/stock-disponible")
def get_stock_disponible(producto_id: int):
    """GET /productos/{id}/stock-disponible — Calcula el stock máximo disponible basado en ingredientes."""
    with Session(engine) as session:
        from app.repositories.producto_repository import ProductoRepository
        repo = ProductoRepository(session)
        stock = repo.get_available_stock(producto_id)
        return {"producto_id": producto_id, "stock_disponible": stock}


@unidades_router.get("/", response_model=list[UnidadMedidaResponse])
def list_unidades_medida():
    """GET /unidades-medida — Lista todas las unidades de medida."""
    with Session(engine) as session:
        unidades = session.exec(select(UnidadMedida)).all()
        return [UnidadMedidaResponse.model_validate(u) for u in unidades]