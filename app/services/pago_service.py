import uuid
import json
import requests
import mercadopago
from fastapi import HTTPException
from sqlmodel import select
from app.core.config import settings
from app.core.ws_manager import ws_manager
from app.models import Pago, Pedido, EstadoPedidoCodigo, HistorialEstadoPedido, RolCodigo, Usuario
from app.repositories import PedidoRepository, UnitOfWork

MP_API_BASE = "https://api.mercadopago.com"


def _get_sdk() -> mercadopago.SDK:
    return mercadopago.SDK(settings.MP_ACCESS_TOKEN)


def _crear_preferencia_mp(preference_data: dict) -> dict:
    """Crea una preferencia en MP usando requests directamente.
    
    El SDK de Python tiene bugs con ciertos campos como auto_return,
    por eso usamos la API REST directamente.
    """
    headers = {
        "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        f"{MP_API_BASE}/checkout/preferences",
        headers=headers,
        data=json.dumps(preference_data),
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        detail = resp.json().get("message", "") if resp.content else ""
        raise HTTPException(
            status_code=502,
            detail=f"Error al crear preferencia en MercadoPago (HTTP {resp.status_code}): {detail}",
        )
    return resp.json()


class PagoService:

    def crear_pago(self, pedido_id: int, current_user: Usuario) -> dict:
        """Crea una preferencia de pago en MercadoPago para un pedido."""
        with UnitOfWork() as uow:
            repo   = PedidoRepository(uow.session)
            pedido = repo.get_with_detalles(pedido_id)

            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            if pedido.usuario_id != current_user.id:
                raise HTTPException(status_code=403, detail="No autorizado")
            if pedido.estado_codigo != EstadoPedidoCodigo.PENDIENTE:
                raise HTTPException(status_code=400, detail="El pedido no está en estado PENDIENTE")

            pago_existente = uow.session.exec(
                select(Pago).where(
                    Pago.pedido_id == pedido_id,
                    Pago.mp_status == "approved",
                )
            ).first()
            if pago_existente:
                raise HTTPException(status_code=400, detail="El pedido ya tiene un pago aprobado")

            external_reference = str(uuid.uuid4())
            idempotency_key    = str(uuid.uuid4())

            preference_data = {
                "items": [
                    {
                        "title":      d.nombre_snapshot,
                        "quantity":   d.cantidad,
                        "unit_price": float(d.precio_snapshot),
                        "currency_id": "ARS",
                    }
                    for d in pedido.detalles
                ],
                "payer": {
                    "email":   current_user.email,
                    "name":    current_user.nombre,
                    "surname": current_user.apellido,
                },
                "auto_return":        "all",
                "external_reference": external_reference,
                "binary_mode":        True,
                "back_urls": {
                    "success": f"{settings.FRONTEND_STORE_URL}/pedidos/{pedido_id}",
                    "failure": f"{settings.FRONTEND_STORE_URL}/pedidos/{pedido_id}",
                    "pending": f"{settings.FRONTEND_STORE_URL}/pedidos/{pedido_id}",
                },
            }
            if settings.MP_NOTIFICATION_URL:
                preference_data["notification_url"] = settings.MP_NOTIFICATION_URL

            preference = _crear_preferencia_mp(preference_data)

            pago = Pago(
                pedido_id=pedido_id,
                mp_status="pending",
                external_reference=external_reference,
                idempotency_key=idempotency_key,
                transaction_amount=float(pedido.total),
            )
            uow.session.add(pago)
            uow.session.flush()
            uow.session.refresh(pago)

            return {
                "pago_id":            pago.id,
                "preference_id":      preference.get("id"),
                "init_point":         preference.get("init_point"),
                "sandbox_init_point": preference.get("sandbox_init_point"),
                "external_reference": external_reference,
                "mp_status":          pago.mp_status,
            }

    async def procesar_webhook(self, topic: str, resource_id: str) -> dict:
        """Procesa el webhook IPN de MercadoPago."""
        if topic != "payment":
            return {"status": "ok", "detail": "topic ignorado"}

        sdk      = _get_sdk()
        response = sdk.payment().get(resource_id)
        if response["status"] != 200:
            raise HTTPException(status_code=502, detail="Error al consultar pago en MercadoPago")

        mp_data          = response["response"]
        mp_status        = mp_data.get("status", "")
        mp_status_detail = mp_data.get("status_detail", "")
        external_ref     = mp_data.get("external_reference", "")
        mp_payment_id    = mp_data.get("id")
        transaction_amt  = float(mp_data.get("transaction_amount", 0))
        payment_method   = mp_data.get("payment_method_id", "")

        pedido_id_ws = None

        with UnitOfWork() as uow:
            pago = uow.session.exec(
                select(Pago).where(Pago.external_reference == external_ref)
            ).first()
            if not pago:
                return {"status": "ok", "detail": "pago no encontrado"}

            pago.mp_payment_id      = mp_payment_id
            pago.mp_status          = mp_status
            pago.mp_status_detail   = mp_status_detail
            pago.transaction_amount = transaction_amt
            pago.payment_method_id  = payment_method
            uow.session.add(pago)

            if mp_status == "approved":
                repo   = PedidoRepository(uow.session)
                pedido = repo.get_with_detalles(pago.pedido_id)
                if pedido and pedido.estado_codigo == EstadoPedidoCodigo.PENDIENTE:
                    pedido.estado_codigo = EstadoPedidoCodigo.CONFIRMADO
                    uow.session.add(pedido)
                    uow.session.flush()
                    repo.append_historial(HistorialEstadoPedido(
                        pedido_id=pedido.id,  # type: ignore
                        estado_desde=EstadoPedidoCodigo.PENDIENTE,
                        estado_hacia=EstadoPedidoCodigo.CONFIRMADO,
                        usuario_id=None,
                        motivo="Pago aprobado por MercadoPago",
                    ))
                    pedido_id_ws = pedido.id

        # RN-06: broadcast FUERA del UoW
        if mp_status == "approved" and pedido_id_ws:
            evento = ws_manager.build_evento(
                event="pago_confirmado",
                pedido_id=pedido_id_ws,
                estado_nuevo=EstadoPedidoCodigo.CONFIRMADO,
                estado_anterior=EstadoPedidoCodigo.PENDIENTE,
                usuario_id=None,
            )
            await ws_manager.broadcast_pedido(pedido_id_ws, evento)

        return {"status": "ok"}

    def verify_pago(self, pedido_id: int, mp_payment_id: str, current_user: Usuario) -> dict:
        """Verifica el estado de un pago contra MercadoPago."""
        broadcast_info = None
        with UnitOfWork() as uow:
            repo = PedidoRepository(uow.session)
            pedido = repo.get_active_by_id(pedido_id)
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            if pedido.usuario_id != current_user.id:
                raise HTTPException(status_code=403, detail="No autorizado")

            pago = uow.session.exec(
                select(Pago).where(Pago.pedido_id == pedido_id)
            ).first()
            if not pago:
                raise HTTPException(status_code=404, detail="Pago no encontrado")

            # Idempotencia: si ya se procesó este payment, devolvé el estado actual
            if pago.mp_payment_id == mp_payment_id and pago.mp_status == "approved":
                return {
                    "status": "approved",
                    "pedido_estado": pedido.estado_codigo.value,
                    "detail": "already_verified",
                    "_broadcast": None,
                }

            sdk = _get_sdk()
            response = sdk.payment().get(mp_payment_id)
            if response["status"] != 200:
                raise HTTPException(status_code=502, detail="Error al consultar pago en MercadoPago")

            mp_data = response["response"]
            mp_status = mp_data.get("status", "")

            pago.mp_payment_id = mp_payment_id
            pago.mp_status = mp_status
            pago.mp_status_detail = mp_data.get("status_detail", "")
            pago.transaction_amount = float(mp_data.get("transaction_amount", 0))
            pago.payment_method_id = mp_data.get("payment_method_id", "")
            uow.session.add(pago)

            if mp_status == "approved" and pedido.estado_codigo == EstadoPedidoCodigo.PENDIENTE:
                pedido.estado_codigo = EstadoPedidoCodigo.CONFIRMADO
                uow.session.add(pedido)
                uow.session.flush()
                repo.append_historial(HistorialEstadoPedido(
                    pedido_id=pedido.id,
                    estado_desde=EstadoPedidoCodigo.PENDIENTE,
                    estado_hacia=EstadoPedidoCodigo.CONFIRMADO,
                    usuario_id=None,
                    motivo="Pago aprobado por MercadoPago (verificación post-pago)",
                ))
                broadcast_info = {
                    "pedido_id": pedido.id,
                    "event": "pago_verificado",
                    "estado_anterior": EstadoPedidoCodigo.PENDIENTE.value,
                    "estado_nuevo": EstadoPedidoCodigo.CONFIRMADO.value,
                    "motivo": "Pago aprobado por MercadoPago",
                }
            elif mp_status in ("rejected", "cancelled", "refunded", "charged_back") and pedido.estado_codigo == EstadoPedidoCodigo.PENDIENTE:
                pedido.estado_codigo = EstadoPedidoCodigo.CANCELADO
                uow.session.add(pedido)
                uow.session.flush()
                repo.append_historial(HistorialEstadoPedido(
                    pedido_id=pedido.id,
                    estado_desde=EstadoPedidoCodigo.PENDIENTE,
                    estado_hacia=EstadoPedidoCodigo.CANCELADO,
                    usuario_id=None,
                    motivo=f"Pago {mp_status} por MercadoPago (verificación post-pago)",
                ))
                broadcast_info = {
                    "pedido_id": pedido.id,
                    "event": "pago_verificado",
                    "estado_anterior": EstadoPedidoCodigo.PENDIENTE.value,
                    "estado_nuevo": EstadoPedidoCodigo.CANCELADO.value,
                    "motivo": f"Pago {mp_status} por MercadoPago",
                }

            return {
                "status": mp_status,
                "pedido_estado": pedido.estado_codigo.value,
                "_broadcast": broadcast_info,
            }

    def get_pago_by_pedido(self, pedido_id: int, current_user: Usuario) -> dict:
        """Devuelve los datos del pago asociado a un pedido."""
        with UnitOfWork() as uow:
            repo   = PedidoRepository(uow.session)
            pedido = repo.get_with_detalles(pedido_id)
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            user_roles = {r.codigo for r in current_user.roles}
            if RolCodigo.CLIENT in user_roles and RolCodigo.ADMIN not in user_roles:
                if pedido.usuario_id != current_user.id:
                    raise HTTPException(status_code=403, detail="No autorizado")

            pago = uow.session.exec(
                select(Pago).where(Pago.pedido_id == pedido_id)
            ).first()
            if not pago:
                raise HTTPException(status_code=404, detail="Pago no encontrado")

            return {
                "id":                 pago.id,
                "pedido_id":          pago.pedido_id,
                "mp_payment_id":      pago.mp_payment_id,
                "mp_status":          pago.mp_status,
                "mp_status_detail":   pago.mp_status_detail,
                "external_reference": pago.external_reference,
                "transaction_amount": pago.transaction_amount,
                "payment_method_id":  pago.payment_method_id,
                "created_at":         pago.created_at,
                "updated_at":         pago.updated_at,
            }