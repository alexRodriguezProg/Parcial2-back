from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.repositories import CategoriaRepository, UnitOfWork
from app.models import Categoria
from app.schemas.schemas import CategoriaCreate, CategoriaUpdate, CategoriaResponse


class CategoriaService:

    def get_all(self, skip=0, limit=100, parent_id=None, include_subcategorias=False) -> tuple:
        """Devuelve categorías con subcategorías anidadas."""
        with UnitOfWork() as uow:
            repo = CategoriaRepository(uow.session)
            categorias, total = repo.get_all_with_filter(
                parent_id=parent_id,
                include_subcategorias=include_subcategorias,
                skip=skip, limit=limit
            )
            items = []
            for cat in categorias:
                subs = repo.get_subcategorias(cat.id)
                cat_data = CategoriaResponse.model_validate(cat).model_dump()
                cat_data["subcategorias"] = [CategoriaResponse.model_validate(s).model_dump() for s in subs]
                items.append(cat_data)
            return total, items

    def get_all_flat(self, search=None) -> list:
        """Devuelve la lista plana de categorías (sin anidar)."""
        with UnitOfWork() as uow:
            cats = CategoriaRepository(uow.session).get_all_flat(search=search)
            return [CategoriaResponse.model_validate(c).model_dump() for c in cats]

    def get_by_id(self, categoria_id: int) -> dict:
        """Devuelve una categoría por ID con subcategorías."""
        with UnitOfWork() as uow:
            repo = CategoriaRepository(uow.session)
            cat = repo.get_active_by_id(categoria_id)
            if not cat:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            subs = repo.get_subcategorias(categoria_id)
            cat_data = CategoriaResponse.model_validate(cat).model_dump()
            cat_data["subcategorias"] = [CategoriaResponse.model_validate(s).model_dump() for s in subs]
            return cat_data

    def create(self, data: CategoriaCreate) -> dict:
        """Crea una categoría nueva."""
        with UnitOfWork() as uow:
            repo = CategoriaRepository(uow.session)
            if data.parent_id and not repo.get_active_by_id(data.parent_id):
                raise HTTPException(status_code=404, detail="Categoría padre no encontrada")
            try:
                cat = repo.create(Categoria(**data.model_dump()))
                uow.session.refresh(cat)
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una categoría con ese nombre."
                )
            return CategoriaResponse.model_validate(cat).model_dump()

    def update(self, categoria_id: int, data: CategoriaUpdate) -> dict:
        """Actualiza una categoría existente."""
        with UnitOfWork() as uow:
            repo = CategoriaRepository(uow.session)
            cat = repo.get_active_by_id(categoria_id)
            if not cat:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            if data.parent_id and data.parent_id == categoria_id:
                raise HTTPException(status_code=400, detail="Una categoría no puede ser su propio padre")
            try:
                cat = repo.update(cat, data.model_dump(exclude_unset=True))
            except IntegrityError:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una categoría con ese nombre."
                )
            return CategoriaResponse.model_validate(cat).model_dump()

    def delete(self, categoria_id: int) -> None:
        """Elimina (soft delete) una categoría."""
        with UnitOfWork() as uow:
            repo = CategoriaRepository(uow.session)
            cat = repo.get_active_by_id(categoria_id)
            if not cat:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            if repo.has_active_productos(categoria_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No se puede eliminar: tiene productos activos"
                )
            repo.soft_delete(cat)