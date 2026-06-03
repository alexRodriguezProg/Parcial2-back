from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.repositories import PedidoRepository, ProductoRepository, UnitOfWork
from app.models import Pedido, DetallePedido, HistorialEstadoPedido, EstadoPedidoCodigo, RolCodigo, FormaPago
from app.schemas.schemas import (
    CrearPedidoRequest, AvanzarEstadoRequest,
    PedidoResponse, PedidoListResponse,
    EstadoPedidoResponse, FormaPagoResponse
)
from sqlmodel import select


class PedidoService:

    def get_all(self, current_user, skip=0, limit=20, estado_codigo=None):
        with UnitOfWork() as uow:
            repo = PedidoRepository(uow.session)
            user_roles = {r.codigo for r in current_user.roles}
            usuario_id = current_user.id if (
                RolCodigo.CLIENT in user_roles and
                RolCodigo.ADMIN not in user_roles and
                RolCodigo.PEDIDOS not in user_roles
            ) else None
            pedidos, total = repo.get_all_with_filters(
                skip=skip, limit=limit,
                usuario_id=usuario_id,
                estado_codigo=estado_codigo
            )
            for p in pedidos:
                _ = p.estado
                _ = p.forma_pago
            items = [PedidoListResponse.model_validate(p).model_dump() for p in pedidos]
            return total, items

    def get_by_id(self, pedido_id: int, current_user):
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

    def crear_pedido(self, data: CrearPedidoRequest, current_user):
        with UnitOfWork() as uow:
            pedido_repo = PedidoRepository(uow.session)
            producto_repo = ProductoRepository(uow.session)

            estado_pendiente = pedido_repo.get_estado_by_codigo(EstadoPedidoCodigo.PENDIENTE)
            if not estado_pendiente:
                raise HTTPException(status_code=500, detail="Estado PENDIENTE no configurado")

            forma_pago = uow.session.exec(
                select(FormaPago).where(FormaPago.id == data.forma_pago_id, FormaPago.activo == True)
            ).first()
            if not forma_pago:
                raise HTTPException(status_code=404, detail="Forma de pago no encontrada")

            detalles_data = []
            total = 0.0
            for item in data.items:
                producto = producto_repo.get_active_by_id(item.producto_id)
                if not producto:
                    raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no encontrado")
                if not producto.disponible:
                    raise HTTPException(status_code=400, detail=f"'{producto.nombre}' no está disponible")
                if producto.stock_cantidad < item.cantidad:
                    raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{producto.nombre}'")
                subtotal = producto.precio * item.cantidad
                total += subtotal
                detalles_data.append({
                    "producto_id": item.producto_id,
                    "precio_unitario": producto.precio,
                    "nombre_producto": producto.nombre,
                    "cantidad": item.cantidad,
                    "subtotal": subtotal,
                })
                producto.stock_cantidad -= item.cantidad
                uow.session.add(producto)

            pedido = pedido_repo.create(Pedido(
                usuario_id=current_user.id, estado_id=estado_pendiente.id,
                forma_pago_id=data.forma_pago_id, direccion_id=data.direccion_id,
                total=total, notas=data.notas,
            ))
            for d in detalles_data:
                pedido_repo.create_detalle(DetallePedido(pedido_id=pedido.id, **d))
            pedido_repo.append_historial(HistorialEstadoPedido(
                pedido_id=pedido.id, estado_id=estado_pendiente.id,
                usuario_id=current_user.id, notas="Pedido creado",
            ))
            uow.session.refresh(pedido)
            _ = pedido.detalles
            _ = pedido.estado
            _ = pedido.forma_pago
            _ = pedido.historial
            return PedidoResponse.model_validate(pedido).model_dump()

    def avanzar_estado(self, pedido_id: int, data: AvanzarEstadoRequest, current_user):
        with UnitOfWork() as uow:
            repo = PedidoRepository(uow.session)
            pedido = repo.get_with_detalles(pedido_id)
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            estado_actual = pedido.estado.codigo
            nuevo_estado_codigo = data.nuevo_estado

            if not repo.can_transition(estado_actual, nuevo_estado_codigo):
                raise HTTPException(status_code=400, detail=f"Transición inválida: {estado_actual} → {nuevo_estado_codigo}")

            user_roles = {r.codigo for r in current_user.roles}
            if nuevo_estado_codigo == EstadoPedidoCodigo.CANCELADO:
                if RolCodigo.CLIENT in user_roles and RolCodigo.ADMIN not in user_roles:
                    if pedido.usuario_id != current_user.id:
                        raise HTTPException(status_code=403, detail="No autorizado")
                    if estado_actual not in [EstadoPedidoCodigo.PENDIENTE, EstadoPedidoCodigo.CONFIRMADO]:
                        raise HTTPException(status_code=400, detail="Solo podés cancelar desde PENDIENTE o CONFIRMADO")

            nuevo_estado = repo.get_estado_by_codigo(nuevo_estado_codigo)
            pedido.estado_id = nuevo_estado.id
            pedido.updated_at = datetime.utcnow()
            uow.session.add(pedido)
            uow.session.flush()
            repo.append_historial(HistorialEstadoPedido(
                pedido_id=pedido.id, estado_id=nuevo_estado.id,
                usuario_id=current_user.id, notas=data.notas,
            ))
            uow.session.refresh(pedido)
            _ = pedido.detalles
            _ = pedido.estado
            _ = pedido.forma_pago
            _ = pedido.historial
            return PedidoResponse.model_validate(pedido).model_dump()

    def get_estados(self):
        with UnitOfWork() as uow:
            estados = PedidoRepository(uow.session).get_all_estados()
            return [EstadoPedidoResponse.model_validate(e).model_dump() for e in estados]

    def get_formas_pago(self):
        with UnitOfWork() as uow:
            formas = PedidoRepository(uow.session).get_all_formas_pago()
            return [FormaPagoResponse.model_validate(f).model_dump() for f in formas]