from typing import Annotated, Optional
from fastapi import APIRouter, Query, status
from app.schemas.schemas import CategoriaCreate, CategoriaUpdate, CategoriaResponse, CategoriaConSubcategorias
from app.services.categoria_service import CategoriaService
from app.core.dependencies import AdminUser

router = APIRouter(prefix="/api/v1/categorias", tags=["categorias"])
service = CategoriaService()


@router.get("/", response_model=dict)
def list_categorias(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    parent_id: Annotated[Optional[int], Query()] = None,
    include_subcategorias: Annotated[bool, Query()] = False,
):
    total, items = service.get_all(skip=skip, limit=limit, parent_id=parent_id, include_subcategorias=include_subcategorias)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/flat", response_model=list[CategoriaResponse])
def list_categorias_flat():
    return service.get_all_flat()


@router.get("/{categoria_id}")
def get_categoria(categoria_id: int):
    return service.get_by_id(categoria_id)


@router.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def create_categoria(data: CategoriaCreate, _: AdminUser = None):
    return service.create(data)


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def update_categoria(categoria_id: int, data: CategoriaUpdate, _: AdminUser = None):
    return service.update(categoria_id, data)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(categoria_id: int, _: AdminUser = None):
    service.delete(categoria_id)