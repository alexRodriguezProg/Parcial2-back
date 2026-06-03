from typing import Annotated, Optional
from fastapi import APIRouter, Query, status
from app.schemas.schemas import (
    ProductoCreate, ProductoUpdate, ProductoDisponibilidadUpdate, ProductoResponse,
    IngredienteCreate, IngredienteUpdate, IngredienteResponse, AddIngredienteRequest,
)
from app.services.producto_service import ProductoService, IngredienteService
from app.dependencies import AdminUser, AdminOrStock

ingredientes_router = APIRouter(prefix="/api/v1/ingredientes", tags=["ingredientes"])
productos_router = APIRouter(prefix="/api/v1/productos", tags=["productos"])

producto_service = ProductoService()
ingrediente_service = IngredienteService()


@ingredientes_router.get("/", response_model=dict)
def list_ingredientes(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    es_alergeno: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
):
    items, total = ingrediente_service.get_all(skip=skip, limit=limit, es_alergeno=es_alergeno, search=search)
    return {"total": total, "skip": skip, "limit": limit, "items": [IngredienteResponse.model_validate(i).model_dump() for i in items]}


@ingredientes_router.get("/{ingrediente_id}", response_model=IngredienteResponse)
def get_ingrediente(ingrediente_id: int):
    return ingrediente_service.get_by_id(ingrediente_id)


@ingredientes_router.post("/", response_model=IngredienteResponse, status_code=status.HTTP_201_CREATED)
def create_ingrediente(data: IngredienteCreate, _: AdminUser):
    return ingrediente_service.create(data)


@ingredientes_router.put("/{ingrediente_id}", response_model=IngredienteResponse)
def update_ingrediente(ingrediente_id: int, data: IngredienteUpdate, _: AdminUser):
    return ingrediente_service.update(ingrediente_id, data)


@ingredientes_router.delete("/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingrediente(ingrediente_id: int, _: AdminUser):
    ingrediente_service.delete(ingrediente_id)


@productos_router.get("/", response_model=dict)
def list_productos(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    categoria_id: Annotated[Optional[int], Query()] = None,
    disponible: Annotated[Optional[bool], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
):
    total, items = producto_service.get_all(skip=skip, limit=limit, categoria_id=categoria_id, disponible=disponible, search=search)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@productos_router.get("/{producto_id}", response_model=ProductoResponse)
def get_producto(producto_id: int):
    return producto_service.get_by_id(producto_id)


@productos_router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(data: ProductoCreate, _: AdminUser):
    return producto_service.create(data)


@productos_router.put("/{producto_id}", response_model=ProductoResponse)
def update_producto(producto_id: int, data: ProductoUpdate, _: AdminUser):
    return producto_service.update(producto_id, data)


@productos_router.patch("/{producto_id}/disponibilidad", response_model=ProductoResponse)
def update_disponibilidad(producto_id: int, data: ProductoDisponibilidadUpdate, _: AdminOrStock):
    return producto_service.update_disponibilidad(producto_id, data)


@productos_router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(producto_id: int, _: AdminUser):
    producto_service.delete(producto_id)


@productos_router.post("/{producto_id}/ingredientes", response_model=ProductoResponse)
def add_ingrediente(producto_id: int, data: AddIngredienteRequest, _: AdminUser):
    return producto_service.add_ingrediente(producto_id, data)


@productos_router.delete("/{producto_id}/ingredientes/{ingrediente_id}", response_model=ProductoResponse)
def remove_ingrediente(producto_id: int, ingrediente_id: int, _: AdminUser):
    return producto_service.remove_ingrediente(producto_id, ingrediente_id)