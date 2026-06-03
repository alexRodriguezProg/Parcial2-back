from fastapi import HTTPException
from app.repositories import DireccionRepository, UnitOfWork
from app.models import DireccionEntrega
from app.schemas.schemas import DireccionCreate, DireccionUpdate, DireccionResponse


class DireccionService:

    def get_all(self, usuario_id: int):
        with UnitOfWork() as uow:
            dirs = DireccionRepository(uow.session).get_by_usuario(usuario_id)
            return [DireccionResponse.model_validate(d).model_dump() for d in dirs]

    def get_by_id(self, direccion_id: int, usuario_id: int):
        with UnitOfWork() as uow:
            d = DireccionRepository(uow.session).get_active_by_id(direccion_id)
            if not d or d.usuario_id != usuario_id:
                raise HTTPException(status_code=404, detail="Dirección no encontrada")
            return DireccionResponse.model_validate(d).model_dump()

    def create(self, data: DireccionCreate, usuario_id: int):
        with UnitOfWork() as uow:
            repo = DireccionRepository(uow.session)
            if data.es_principal:
                repo.clear_principal(usuario_id)
            d = repo.create(DireccionEntrega(usuario_id=usuario_id, **data.model_dump()))
            uow.session.refresh(d)
            return DireccionResponse.model_validate(d).model_dump()

    def update(self, direccion_id: int, data: DireccionUpdate, usuario_id: int):
        with UnitOfWork() as uow:
            repo = DireccionRepository(uow.session)
            d = repo.get_active_by_id(direccion_id)
            if not d or d.usuario_id != usuario_id:
                raise HTTPException(status_code=404, detail="Dirección no encontrada")
            d = repo.update(d, data.model_dump(exclude_unset=True))
            return DireccionResponse.model_validate(d).model_dump()

    def set_principal(self, direccion_id: int, usuario_id: int):
        with UnitOfWork() as uow:
            repo = DireccionRepository(uow.session)
            d = repo.get_active_by_id(direccion_id)
            if not d or d.usuario_id != usuario_id:
                raise HTTPException(status_code=404, detail="Dirección no encontrada")
            repo.clear_principal(usuario_id)
            d.es_principal = True
            uow.session.add(d)
            uow.session.flush()
            uow.session.refresh(d)
            return DireccionResponse.model_validate(d).model_dump()

    def delete(self, direccion_id: int, usuario_id: int):
        with UnitOfWork() as uow:
            repo = DireccionRepository(uow.session)
            d = repo.get_active_by_id(direccion_id)
            if not d or d.usuario_id != usuario_id:
                raise HTTPException(status_code=404, detail="Dirección no encontrada")
            repo.soft_delete(d)