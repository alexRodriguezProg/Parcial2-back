from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging_config import logger


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja HTTPException (404, 401, 403, 409, 422, 429, etc.). RFC 7807."""
    logger.warning(
        f"HTTPException {exc.status_code} en {request.method} {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "path": str(request.url.path),
        },
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic (422)."""
    errors = exc.errors()
    logger.warning(f"ValidationError en {request.method} {request.url.path}: {errors}")
    primer_error = errors[0] if errors else {}
    campo = ".".join(str(loc) for loc in primer_error.get("loc", []) if loc != "body")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación en los datos enviados",
            "code": "VALIDATION_ERROR",
            "field": campo or None,
            "errors": errors,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción no manejada (500 inesperados)."""
    logger.error(
        f"Excepción no controlada en {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ocurrió un error interno en el servidor",
            "code": "INTERNAL_SERVER_ERROR",
            "path": str(request.url.path),
        },
    )