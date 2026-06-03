from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class RolCodigo(str, Enum):
    ADMIN = "ADMIN"
    STOCK = "STOCK"
    PEDIDOS = "PEDIDOS"
    CLIENT = "CLIENT"

class EstadoPedidoCodigo(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREP = "EN_PREP"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

class FormaPagoCodigo(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    MERCADOPAGO = "MERCADOPAGO"



class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id", primary_key=True)
    rol_id: Optional[int] = Field(default=None, foreign_key="rol.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"
    producto_id: Optional[int] = Field(default=None, foreign_key="producto.id", primary_key=True)
    ingrediente_id: Optional[int] = Field(default=None, foreign_key="ingrediente.id", primary_key=True)
    cantidad: Optional[str] = Field(default=None)


class Rol(SQLModel, table=True):
    __tablename__ = "rol"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50)
    codigo: RolCodigo = Field(unique=True)
    descripcion: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    usuarios: List["Usuario"] = Relationship(back_populates="roles", link_model=UsuarioRol)

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255)
    password_hash: str = Field(max_length=255)
    telefono: Optional[str] = Field(default=None, max_length=20)
    activo: bool = Field(default=True)
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    roles: List[Rol] = Relationship(back_populates="usuarios", link_model=UsuarioRol)
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")
    direcciones: List["DireccionEntrega"] = Relationship(back_populates="usuario")

class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    descripcion: Optional[str] = Field(default=None)
    imagen_url: Optional[str] = Field(default=None)
    parent_id: Optional[int] = Field(default=None, foreign_key="categoria.id")
    activo: bool = Field(default=True)
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    productos: List["Producto"] = Relationship(back_populates="categoria")

class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingrediente"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    descripcion: Optional[str] = Field(default=None)
    es_alergeno: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    productos: List["Producto"] = Relationship(back_populates="ingredientes", link_model=ProductoIngrediente)

class Producto(SQLModel, table=True):
    __tablename__ = "producto"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=200)
    descripcion: Optional[str] = Field(default=None)
    precio: float = Field(ge=0)
    imagen_url: Optional[str] = Field(default=None)
    stock_cantidad: int = Field(default=0, ge=0)
    disponible: bool = Field(default=True)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categoria.id")
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    categoria: Optional[Categoria] = Relationship(back_populates="productos")
    ingredientes: List[Ingrediente] = Relationship(back_populates="productos", link_model=ProductoIngrediente)
    detalles_pedido: List["DetallePedido"] = Relationship(back_populates="producto")

class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direccion_entrega"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    alias: str = Field(max_length=50, default="Casa")
    calle: str = Field(max_length=200)
    numero: str = Field(max_length=20)
    piso: Optional[str] = Field(default=None, max_length=20)
    ciudad: str = Field(max_length=100)
    provincia: str = Field(max_length=100)
    codigo_postal: Optional[str] = Field(default=None, max_length=20)
    es_principal: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    usuario: Optional[Usuario] = Relationship(back_populates="direcciones")
    pedidos: List["Pedido"] = Relationship(back_populates="direccion")

class FormaPago(SQLModel, table=True):
    __tablename__ = "forma_pago"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    codigo: FormaPagoCodigo = Field(unique=True)
    activo: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pedidos: List["Pedido"] = Relationship(back_populates="forma_pago")

class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50)
    codigo: EstadoPedidoCodigo = Field(unique=True)
    descripcion: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pedidos: List["Pedido"] = Relationship(back_populates="estado")
    historial: List["HistorialEstadoPedido"] = Relationship(back_populates="estado")

class Pedido(SQLModel, table=True):
    __tablename__ = "pedido"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    estado_id: int = Field(foreign_key="estado_pedido.id")
    forma_pago_id: int = Field(foreign_key="forma_pago.id")
    direccion_id: Optional[int] = Field(default=None, foreign_key="direccion_entrega.id")
    total: float = Field(ge=0)
    notas: Optional[str] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    usuario: Optional[Usuario] = Relationship(back_populates="pedidos")
    estado: Optional[EstadoPedido] = Relationship(back_populates="pedidos")
    forma_pago: Optional[FormaPago] = Relationship(back_populates="pedidos")
    direccion: Optional[DireccionEntrega] = Relationship(back_populates="pedidos")
    detalles: List["DetallePedido"] = Relationship(back_populates="pedido")
    historial: List["HistorialEstadoPedido"] = Relationship(back_populates="pedido")

class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id")
    producto_id: int = Field(foreign_key="producto.id")
    precio_unitario: float = Field(ge=0)   # snapshot
    nombre_producto: str = Field(max_length=200)  # snapshot
    cantidad: int = Field(ge=1)
    subtotal: float = Field(ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pedido: Optional[Pedido] = Relationship(back_populates="detalles")
    producto: Optional[Producto] = Relationship(back_populates="detalles_pedido")

class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido"
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id")
    estado_id: int = Field(foreign_key="estado_pedido.id")
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    notas: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pedido: Optional[Pedido] = Relationship(back_populates="historial")
    estado: Optional[EstadoPedido] = Relationship(back_populates="historial")