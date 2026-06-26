from typing import Optional
from datetime import datetime
from fastapi import HTTPException
from app.repositories import PedidoRepository, ProductoRepository, UnitOfWork
from app.models import (
    Pedido, DetallePedido, HistorialEstadoPedido,
    EstadoPedidoCodigo, RolCodigo, FormaPago, Usuario,
)
from app.schemas.schemas import (
    CrearPedidoRequest, AvanzarEstadoRequest,
    PedidoResponse, PedidoListResponse,
    EstadoPedidoResponse, FormaPagoResponse,
)
from app.core.ws_manager import ws_manager
from sqlmodel import select


FSM: dict[EstadoPedidoCodigo, set[EstadoPedidoCodigo]] = {
    EstadoPedidoCodigo.PENDIENTE:  {EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.CANCELADO},
    EstadoPedidoCodigo.CONFIRMADO: {EstadoPedidoCodigo.EN_PREP,    EstadoPedidoCodigo.CANCELADO},
    EstadoPedidoCodigo.EN_PREP:    {EstadoPedidoCodigo.ENTREGADO,  EstadoPedidoCodigo.CANCELADO},
    EstadoPedidoCodigo.ENTREGADO:  set(),
    EstadoPedidoCodigo.CANCELADO:  set(),
}


class PedidoService:

    def get_all(self, current_user: Usuario, skip=0, limit=20, estado_codigo=None, search=None) -> tuple:
        """Devuelve pedidos con filtros opcionales."""
        with UnitOfWork() as uow:
            repo = PedidoRepository(uow.session)
            user_roles = {r.codigo for r in current_user.roles}
            usuario_id = current_user.id if (
                RolCodigo.CLIENT in user_roles
                and RolCodigo.ADMIN not in user_roles
                and RolCodigo.PEDIDOS not in user_roles
            ) else None
            pedidos, total = repo.get_all_with_filters(
                skip=skip, limit=limit,
                usuario_id=usuario_id,
                estado_codigo=estado_codigo,
                search=search,
            )
            for p in pedidos:
                _ = p.estado
                _ = p.forma_pago
            items = [PedidoListResponse.model_validate(p).model_dump() for p in pedidos]
            return total, items

    def get_by_id(self, pedido_id: int, current_user: Usuario) -> dict:
        """Devuelve un pedido con detalles e historial."""
        with UnitOfWork() as uow:
            repo = PedidoRepository(uow.session)
            pedido = repo.get_with_detalles(pedido_id)
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            user_roles = {r.codigo for r in current_user.roles}
            if RolCodigo.CLIENT in user_roles and RolCodigo.ADMIN not in user_roles:
                if pedido.usuario_id != current_user.id:
                    raise HTTPException(status_code=403, detail="No autorizado")
            return PedidoResponse.model_validate(pedido).model_dump()

    def crear_pedido(self, data: CrearPedidoRequest, current_user: Usuario) -> dict:
        """Crea un pedido nuevo con sus detalles."""
        with UnitOfWork() as uow:
            pedido_repo   = PedidoRepository(uow.session)
            producto_repo = ProductoRepository(uow.session)

            estado_pendiente = pedido_repo.get_estado_by_codigo(EstadoPedidoCodigo.PENDIENTE)
            if not estado_pendiente:
                raise HTTPException(status_code=500, detail="Estado PENDIENTE no configurado")

            forma_pago = uow.session.exec(
                select(FormaPago).where(
                    FormaPago.codigo == data.forma_pago_codigo, # type: ignore
                    FormaPago.habilitado == True,
                )
            ).first()
            if not forma_pago:
                raise HTTPException(status_code=404, detail="Forma de pago no encontrada")

            detalles_data = []
            subtotal = 0.0
            for item in data.items:
                producto = producto_repo.get_active_by_id(item.producto_id)
                if not producto:
                    raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no encontrado")
                if not producto.disponible:
                    raise HTTPException(status_code=400, detail=f"'{producto.nombre}' no está disponible")
                if producto.stock_cantidad < item.cantidad:
                    raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{producto.nombre}'")

                item_subtotal = producto.precio_base * item.cantidad
                subtotal += item_subtotal
                detalles_data.append({
                    "producto_id":     item.producto_id,
                    "cantidad":        item.cantidad,
                    "nombre_snapshot": producto.nombre,
                    "precio_snapshot": producto.precio_base,
                    "subtotal_snap":   item_subtotal,
                    "personalizacion": item.personalizacion, # type: ignore
                })
                producto.stock_cantidad -= item.cantidad
                producto.disponible = producto.stock_cantidad > 0
                uow.session.add(producto)

            descuento   = 0.0
            costo_envio = 0.0  # Sin lógica de envío implementada aún
            total = subtotal - descuento + costo_envio

            pedido = pedido_repo.create(Pedido(
                usuario_id=current_user.id,
                estado_codigo=EstadoPedidoCodigo.PENDIENTE,
                forma_pago_codigo=data.forma_pago_codigo, # type: ignore
                direccion_id=data.direccion_id,
                subtotal=subtotal,
                descuento=descuento,
                costo_envio=costo_envio,
                total=total,
                notas=data.notas,
            ))

            for d in detalles_data:
                pedido_repo.create_detalle(DetallePedido(pedido_id=pedido.id, **d)) # type: ignore

            # RN-02: primer historial con estado_desde=None
            pedido_repo.append_historial(HistorialEstadoPedido(
                pedido_id=pedido.id, # type: ignore
                estado_desde=None,
                estado_hacia=EstadoPedidoCodigo.PENDIENTE,
                usuario_id=current_user.id,
                motivo="Pedido creado",
            ))

            uow.session.refresh(pedido)
            _ = pedido.detalles
            _ = pedido.estado
            _ = pedido.forma_pago
            _ = pedido.historial
            result = PedidoResponse.model_validate(pedido).model_dump()

        return result

    async def avanzar_estado(self, pedido_id: int, data: AvanzarEstadoRequest, current_user: Usuario) -> dict:
        """Avanza el estado de un pedido validando la FSM."""
        estado_anterior_codigo = None

        with UnitOfWork() as uow:
            repo   = PedidoRepository(uow.session)
            pedido = repo.get_with_detalles(pedido_id)
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            estado_actual = pedido.estado_codigo
            nuevo_estado  = data.nuevo_estado

            # RN-01: estado terminal no admite transiciones
            estado_obj = repo.get_estado_by_codigo(estado_actual)
            if estado_obj and estado_obj.es_terminal:
                raise HTTPException(
                    status_code=422,
                    detail=f"El estado {estado_actual} es terminal y no admite transiciones",
                )

            # Validar FSM
            if nuevo_estado not in FSM.get(estado_actual, set()):
                raise HTTPException(
                    status_code=422,
                    detail=f"Transición inválida: {estado_actual} → {nuevo_estado}",
                )

            # RN-05: motivo obligatorio al cancelar
            if nuevo_estado == EstadoPedidoCodigo.CANCELADO and not data.motivo : # type: ignore
                raise HTTPException(
                    status_code=422,
                    detail="El motivo es obligatorio al cancelar un pedido",
                )

            user_roles = {r.codigo for r in current_user.roles}

            # Solo ADMIN/PEDIDOS pueden cancelar desde EN_PREP
            if (
                nuevo_estado == EstadoPedidoCodigo.CANCELADO
                and estado_actual == EstadoPedidoCodigo.EN_PREP
                and RolCodigo.ADMIN not in user_roles
                and RolCodigo.PEDIDOS not in user_roles
            ):
                raise HTTPException(status_code=403, detail="Solo ADMIN o PEDIDOS pueden cancelar desde EN_PREP")

            # CLIENT solo puede cancelar su propio pedido
            if nuevo_estado == EstadoPedidoCodigo.CANCELADO:
                if RolCodigo.CLIENT in user_roles and RolCodigo.ADMIN not in user_roles:
                    if pedido.usuario_id != current_user.id:
                        raise HTTPException(status_code=403, detail="No autorizado")

            estado_anterior_codigo = estado_actual
            pedido.estado_codigo   = nuevo_estado
            pedido.updated_at      = datetime.utcnow()
            uow.session.add(pedido)
            uow.session.flush()

            # RN-03: append-only
            repo.append_historial(HistorialEstadoPedido(
                pedido_id=pedido.id, # type: ignore
                estado_desde=estado_actual,
                estado_hacia=nuevo_estado,
                usuario_id=current_user.id,
                motivo=data.motivo, # type: ignore
            ))

            uow.session.refresh(pedido)
            _ = pedido.detalles
            _ = pedido.estado
            _ = pedido.forma_pago
            _ = pedido.historial
            result = PedidoResponse.model_validate(pedido).model_dump()

        # RN-06: broadcast FUERA del UoW, post-commit
        evento = ws_manager.build_evento(
            event="pedido_cancelado" if nuevo_estado == EstadoPedidoCodigo.CANCELADO else "estado_cambiado",
            pedido_id=pedido_id,
            estado_nuevo=nuevo_estado,
            estado_anterior=estado_anterior_codigo,
            usuario_id=current_user.id,
            motivo=data.motivo, # type: ignore
        )
        await ws_manager.broadcast_pedido(pedido_id, evento)

        return result

    def get_estados(self) -> list:
        """Devuelve todos los estados de pedido disponibles."""
        with UnitOfWork() as uow:
            estados = PedidoRepository(uow.session).get_all_estados()
            return [EstadoPedidoResponse.model_validate(e).model_dump() for e in estados]

    def get_formas_pago(self) -> list:
        """Devuelve todas las formas de pago habilitadas."""
        with UnitOfWork() as uow:
            formas = PedidoRepository(uow.session).get_all_formas_pago()
            return [FormaPagoResponse.model_validate(f).model_dump() for f in formas]