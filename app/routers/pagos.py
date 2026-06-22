from fastapi import APIRouter, Request, status
from app.services.pago_service import PagoService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1/pagos", tags=["pagos"])
service = PagoService()


@router.post("/crear/{pedido_id}", status_code=status.HTTP_201_CREATED)
def crear_pago(pedido_id: int, current_user: CurrentUser):
    return service.crear_pago(pedido_id, current_user)


@router.post("/webhook")
async def webhook(request: Request):
   
    params      = dict(request.query_params)
    topic       = params.get("topic") or params.get("type", "")
    resource_id = params.get("id") or params.get("data.id", "")
    return await service.procesar_webhook(topic, resource_id)


@router.get("/{pedido_id}")
def get_pago(pedido_id: int, current_user: CurrentUser):
    return service.get_pago_by_pedido(pedido_id, current_user)