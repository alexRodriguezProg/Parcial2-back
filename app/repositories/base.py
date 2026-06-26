from typing import TypeVar, Generic, Type, Optional, List
from sqlmodel import SQLModel, Session, select
from datetime import datetime

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: int) -> Optional[T]:
        """Devuelve un registro por ID (incluye eliminados)."""
        return self.session.get(self.model, id)

    def get_active_by_id(self, id: int) -> Optional[T]:
        """Devuelve un registro activo (no eliminado) por ID."""
        obj = self.session.get(self.model, id)
        if obj and hasattr(obj, "deleted_at") and obj.deleted_at is not None:
            return None
        return obj

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Devuelve todos los registros activos con paginación."""
        statement = select(self.model)
        if hasattr(self.model, "deleted_at"):
            statement = statement.where(self.model.deleted_at == None)
        return self.session.exec(statement.offset(skip).limit(limit)).all()

    def create(self, obj: T) -> T:
        """Persiste un nuevo registro."""
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def update(self, obj: T, data: dict) -> T:
        """Actualiza un registro con un dict de campos."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        if hasattr(obj, "updated_at"):
            obj.updated_at = datetime.utcnow()
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def soft_delete(self, obj: T) -> T:
        """Marca un registro como eliminado (borrado lógico)."""
        obj.deleted_at = datetime.utcnow()
        self.session.add(obj)
        self.session.flush()
        return obj

    def hard_delete(self, obj: T) -> None:
        """Elimina un registro físicamente de la BD."""
        self.session.delete(obj)
        self.session.flush()