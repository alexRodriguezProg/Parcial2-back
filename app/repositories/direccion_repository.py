from typing import List
from sqlmodel import Session, select
from app.repositories.base import BaseRepository
from app.models import DireccionEntrega


class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session: Session):
        super().__init__(DireccionEntrega, session)

    def get_by_usuario(self, usuario_id: int) -> List[DireccionEntrega]:
        """Devuelve las direcciones activas de un usuario."""
        return self.session.exec(
            select(DireccionEntrega).where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.deleted_at == None
            )
        ).all()

    def clear_principal(self, usuario_id: int) -> None:
        """Desmarca todas las direcciones de un usuario como principal."""
        for d in self.get_by_usuario(usuario_id):
            d.es_principal = False
            self.session.add(d)
        self.session.flush()