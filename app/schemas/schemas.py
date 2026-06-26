from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.models.models import RolCodigo, EstadoPedidoCodigo, FormaPagoCodigo


class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    telefono: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RolResponse(BaseModel):
    codigo: RolCodigo
    nombre: str
    class Config:
        from_attributes = True


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    celular: Optional[str] = None
    activo: bool
    created_at: datetime
    roles: List[RolResponse] = []
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class UsuarioUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None


class AsignarRolRequest(BaseModel):
    rol_codigo: RolCodigo


class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    imagen_url: Optional[str]
    parent_id: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True


class CategoriaConSubcategorias(CategoriaResponse):
    subcategorias: List[CategoriaResponse] = []


class IngredienteCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    es_alergeno: bool = False


class IngredienteUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    es_alergeno: Optional[bool] = None


class IngredienteResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    es_alergeno: bool
    created_at: datetime
    class Config:
        from_attributes = True


class AddIngredienteRequest(BaseModel):
    ingrediente_id: int
    cantidad: Optional[float] = None


class AddCategoriaRequest(BaseModel):
    categoria_id: int
    es_principal: bool = True


class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    imagenes_url: Optional[List[str]] = None
    stock_cantidad: int = 0
    disponible: bool = True
    unidad_venta_id: Optional[int] = None
    categoria_ids: Optional[List[int]] = None
    ingredientes: Optional[List[AddIngredienteRequest]] = None


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
    imagenes_url: Optional[List[str]] = None
    stock_cantidad: Optional[int] = None
    disponible: Optional[bool] = None
    unidad_venta_id: Optional[int] = None


class ProductoDisponibilidadUpdate(BaseModel):
    disponible: bool
    stock_cantidad: Optional[int] = None


class ProductoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio_base: float
    imagenes_url: Optional[List[str]]
    stock_cantidad: int
    disponible: bool
    unidad_venta_id: Optional[int]
    categorias: List[CategoriaResponse] = []
    ingredientes: List[IngredienteResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True


class DireccionCreate(BaseModel):
    alias: Optional[str] = "Casa"
    linea1: str
    linea2: Optional[str] = None
    ciudad: str
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    es_principal: bool = False


class DireccionUpdate(BaseModel):
    alias: Optional[str] = None
    linea1: Optional[str] = None
    linea2: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None


class DireccionResponse(BaseModel):
    id: int
    alias: Optional[str]
    linea1: str
    linea2: Optional[str]
    ciudad: str
    provincia: Optional[str]
    codigo_postal: Optional[str]
    es_principal: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ItemCarrito(BaseModel):
    producto_id: int
    cantidad: int
    personalizacion: Optional[List[int]] = None

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v):
        if v < 1:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v


class CrearPedidoRequest(BaseModel):
    items: List[ItemCarrito]
    forma_pago_codigo: FormaPagoCodigo
    direccion_id: Optional[int] = None
    notas: Optional[str] = None


class AvanzarEstadoRequest(BaseModel):
    nuevo_estado: EstadoPedidoCodigo
    motivo: Optional[str] = None


class EstadoPedidoResponse(BaseModel):
    codigo: EstadoPedidoCodigo
    descripcion: str
    orden: int
    es_terminal: bool
    class Config:
        from_attributes = True


class FormaPagoResponse(BaseModel):
    codigo: FormaPagoCodigo
    descripcion: str
    habilitado: bool
    class Config:
        from_attributes = True


class DetallePedidoResponse(BaseModel):
    producto_id: int
    cantidad: int
    nombre_snapshot: str
    precio_snapshot: float
    subtotal_snap: float
    personalizacion: Optional[List[int]] = None
    model_config = {"from_attributes": True}


class HistorialEstadoResponse(BaseModel):
    id: int
    estado_desde: Optional[EstadoPedidoCodigo] = None
    estado_hacia: EstadoPedidoCodigo
    motivo: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    id: int
    usuario_id: int
    estado_codigo: EstadoPedidoCodigo
    forma_pago_codigo: FormaPagoCodigo
    subtotal: float
    descuento: float
    costo_envio: float
    total: float
    notas: Optional[str] = None
    detalles: List[DetallePedidoResponse] = []
    historial: List[HistorialEstadoResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PedidoListResponse(BaseModel):
    id: int
    usuario_id: int
    estado_codigo: EstadoPedidoCodigo
    forma_pago_codigo: FormaPagoCodigo
    total: float
    created_at: datetime
    model_config = {"from_attributes": True}