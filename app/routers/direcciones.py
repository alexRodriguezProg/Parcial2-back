from fastapi import APIRouter, status
from app.schemas.schemas import DireccionCreate, DireccionUpdate, DireccionResponse
from app.services.direccion_service import DireccionService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1/direcciones", tags=["direcciones"])
service = DireccionService()


@router.get("/", response_model=list[DireccionResponse])
def list_direcciones(current_user: CurrentUser):
    return service.get_all(current_user.id) # type: ignore


@router.get("/{direccion_id}", response_model=DireccionResponse)
def get_direccion(direccion_id: int, current_user: CurrentUser):
    return service.get_by_id(direccion_id, current_user.id) # type: ignore


@router.post("/", response_model=DireccionResponse, status_code=status.HTTP_201_CREATED)
def create_direccion(data: DireccionCreate, current_user: CurrentUser):
    return service.create(data, current_user.id) # type: ignore


@router.put("/{direccion_id}", response_model=DireccionResponse)
def update_direccion(direccion_id: int, data: DireccionUpdate, current_user: CurrentUser):
    return service.update(direccion_id, data, current_user.id) # type: ignore


@router.patch("/{direccion_id}/principal", response_model=DireccionResponse)
def set_principal(direccion_id: int, current_user: CurrentUser):
    return service.set_principal(direccion_id, current_user.id) # type: ignore


@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_direccion(direccion_id: int, current_user: CurrentUser):
    service.delete(direccion_id, current_user.id) # type: ignore