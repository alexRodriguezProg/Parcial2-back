from fastapi import APIRouter, UploadFile, File, Query, status
from app.services.upload_service import UploadService
from app.core.dependencies import AdminUser

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])
service = UploadService()


@router.post("/imagen", status_code=status.HTTP_201_CREATED)
async def upload_imagen(
    file:   UploadFile = File(...),
    folder: str        = Query(default="foodstore/productos"),
    _:      AdminUser  = None, # type: ignore
):
    
    return await service.upload_imagen(file, folder)


@router.delete("/imagen/{public_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imagen(public_id: str, _: AdminUser = None): # type: ignore
    
    service.delete_imagen(public_id)