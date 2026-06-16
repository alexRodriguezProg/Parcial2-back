from typing import Optional, List
from sqlmodel import Session, select, func
from app.repositories.base import BaseRepository
from app.models import (
    Pedido, DetallePedido, HistorialEstadoPedido,
    EstadoPedido, EstadoPedidoCodigo, FormaPago,
)


class PedidoRepository(BaseRepository[Pedido]):

    def __init__(self, session: Session):
        super().__init__(Pedido, session)

    def get_all_with_filters(self, skip=0, limit=20, usuario_id=None, estado_codigo=None):
        statement = select(Pedido).where(Pedido.deleted_at == None)
        if usuario_id is not None:
            statement = statement.where(Pedido.usuario_id == usuario_id)
        if estado_codigo:
            statement = statement.where(Pedido.estado_codigo == estado_codigo)
        statement = statement.order_by(Pedido.created_at.desc())
        total   = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        pedidos = self.session.exec(statement.offset(skip).limit(limit)).all()
        return pedidos, total

    def get_with_detalles(self, pedido_id: int) -> Optional[Pedido]:
        pedido = self.session.exec(
            select(Pedido).where(Pedido.id == pedido_id, Pedido.deleted_at == None)
        ).first()
        if pedido:
            _ = pedido.detalles
            _ = pedido.historial
            _ = pedido.estado
            _ = pedido.forma_pago
        return pedido

    def get_estado_by_codigo(self, codigo: EstadoPedidoCodigo) -> Optional[EstadoPedido]:
        return self.session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == codigo)
        ).first()

    def get_all_estados(self) -> List[EstadoPedido]:
        return self.session.exec(select(EstadoPedido).order_by(EstadoPedido.orden)).all()

    def get_all_formas_pago(self) -> List[FormaPago]:
        return self.session.exec(
            select(FormaPago).where(FormaPago.habilitado == True)
        ).all()

    def create_detalle(self, detalle: DetallePedido) -> DetallePedido:
        self.session.add(detalle)
        self.session.flush()
        return detalle

    def append_historial(self, historial: HistorialEstadoPedido) -> HistorialEstadoPedido:
        self.session.add(historial)
        self.session.flush()
        return historial

    def get_historial(self, pedido_id: int) -> List[HistorialEstadoPedido]:
        return self.session.exec(
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.created_at.asc())
        ).all()