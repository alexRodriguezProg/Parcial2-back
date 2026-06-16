from typing import Annotated, Optional
from fastapi import APIRouter, Query, status
from app.schemas.schemas import CrearPedidoRequest, AvanzarEstadoRequest
from app.services.pedido_service import PedidoService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1/pedidos", tags=["pedidos"])
service = PedidoService()


@router.get("/estados")
def list_estados():
    return service.get_estados()


@router.get("/formas-pago")
def list_formas_pago():
    return service.get_formas_pago()


@router.get("/")
def list_pedidos(
    current_user:  CurrentUser,
    skip:          Annotated[int, Query(ge=0)]         = 0,
    limit:         Annotated[int, Query(ge=1, le=100)] = 20,
    estado_codigo: Annotated[Optional[str], Query()]   = None,
):
    total, items = service.get_all(
        current_user=current_user, skip=skip, limit=limit, estado_codigo=estado_codigo
    )
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/{pedido_id}")
def get_pedido(pedido_id: int, current_user: CurrentUser):
    return service.get_by_id(pedido_id, current_user)


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_pedido(data: CrearPedidoRequest, current_user: CurrentUser):
    return service.crear_pedido(data, current_user)


@router.patch("/{pedido_id}/estado")
async def avanzar_estado(pedido_id: int, data: AvanzarEstadoRequest, current_user: CurrentUser):
    return await service.avanzar_estado(pedido_id, data, current_user)


@router.get("/{pedido_id}/historial")
def get_historial(pedido_id: int, current_user: CurrentUser):
    return service.get_by_id(pedido_id, current_user)