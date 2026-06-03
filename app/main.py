from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import create_db_and_tables
from app.routers.auth import router as auth_router
from app.routers.categorias import router as categorias_router
from app.routers.productos import ingredientes_router, productos_router
from app.routers.pedidos import router as pedidos_router
from app.routers.direcciones import router as direcciones_router
from app.routers.admin import router as admin_router

app = FastAPI(
    title = "Parcial 2 API",
)

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

app.include_router(auth_router)
app.include_router(categorias_router)
app.include_router(ingredientes_router)
app.include_router(productos_router)
app.include_router(pedidos_router)
app.include_router(direcciones_router)
app.include_router(admin_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables

@app.get("/")
def root():
    return{"message": "API funcionando"}