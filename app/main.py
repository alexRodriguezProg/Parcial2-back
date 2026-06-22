from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.logging_config import logger
from app.core.middleware import TimingLoggingMiddleware
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

from app.routers.auth import router as auth_router
from app.routers.categorias import router as categorias_router
from app.routers.productos import ingredientes_router, productos_router
from app.routers.pedidos import router as pedidos_router
from app.routers.direcciones import router as direcciones_router
from app.routers.admin import router as admin_router
from app.routers.ws import router as ws_router
from app.routers.pagos import router as pagos_router
from app.routers.uploads import router as uploads_router
from app.routers.estadisticas import router as estadisiticas_router

app = FastAPI(title="Food Store API")


app.add_middleware(TimingLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_STORE_URL,
        settings.FRONTEND_ADMIN_URL,
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


app.include_router(auth_router)
app.include_router(categorias_router)
app.include_router(ingredientes_router)
app.include_router(productos_router)
app.include_router(pedidos_router)
app.include_router(direcciones_router)
app.include_router(admin_router)
app.include_router(ws_router)
app.include_router(pagos_router)
app.include_router(uploads_router)
app.include_router(estadisiticas_router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    logger.info("🍔 Food Store API iniciada correctamente")


@app.get("/")
def root():
    return {"message": "Food Store API funcionando"}