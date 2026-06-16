import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile
from app.core.config import settings

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _init_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )


class UploadService:

    async def upload_imagen(self, file: UploadFile, folder: str = "foodstore/productos") -> dict:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido: {file.content_type}. Usar jpg, png o webp.",
            )

        contenido = await file.read()
        if len(contenido) > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="El archivo supera el tamaño máximo de 5 MB.",
            )

        _init_cloudinary()

        try:
            resultado = cloudinary.uploader.upload(
                contenido,
                folder=folder,
                resource_type="image",
                allowed_formats=["jpg", "jpeg", "png", "webp"],
                overwrite=False,
                unique_filename=True,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error al subir imagen a Cloudinary: {str(e)}")

        return {
            "secure_url":    resultado.get("secure_url"),
            "public_id":     resultado.get("public_id"),
            "width":         resultado.get("width"),
            "height":        resultado.get("height"),
            "format":        resultado.get("format"),
            "resource_type": resultado.get("resource_type"),
        }

    def delete_imagen(self, public_id: str) -> None:
        _init_cloudinary()
        try:
            resultado = cloudinary.uploader.destroy(public_id, resource_type="image")
            if resultado.get("result") not in ("ok", "not found"):
                raise HTTPException(status_code=502, detail="Error al eliminar imagen de Cloudinary")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error al eliminar imagen: {str(e)}")