from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from app.services.pago_service import PagoService
from app.core.dependencies import CurrentUser
from app.core.ws_manager import ws_manager

router = APIRouter(prefix="/api/v1/pagos", tags=["pagos"])
service = PagoService()


class VerifyPagoRequest(BaseModel):
    mp_payment_id: str


@router.post("/crear/{pedido_id}", status_code=status.HTTP_201_CREATED)
def crear_pago(pedido_id: int, current_user: CurrentUser):
    """POST /pagos/crear/{pedido_id} — Crea un pago para un pedido."""
    return service.crear_pago(pedido_id, current_user)


@router.post("/webhook")
async def webhook(request: Request):
    """Endpoint IPN de MercadoPago. Recibe ?topic=payment&id=<payment_id>"""
    params      = dict(request.query_params)
    topic       = params.get("topic") or params.get("type", "")
    resource_id = params.get("id") or params.get("data.id", "")
    return await service.procesar_webhook(topic, resource_id)


@router.post("/verify/{pedido_id}")
async def verify_pago(pedido_id: int, body: VerifyPagoRequest, current_user: CurrentUser):
    """Verifica el pago con MP usando el payment_id que llegó en el redirect.
    Útil como fallback si el webhook no se disparó."""
    try:
        result = service.verify_pago(pedido_id, body.mp_payment_id, current_user)
        bc = result.pop("_broadcast", None)
        if bc:
            evento = ws_manager.build_evento(**bc)
            await ws_manager.broadcast_pedido(bc["pedido_id"], evento)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {type(e).__name__}: {str(e)[:300]}")


@router.get("/{pedido_id}")
def get_pago(pedido_id: int, current_user: CurrentUser):
    """GET /pagos/{pedido_id} — Obtiene el pago asociado a un pedido."""
    return service.get_pago_by_pedido(pedido_id, current_user)