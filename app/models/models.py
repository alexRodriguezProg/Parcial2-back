from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Text, JSON   
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────────────

class RolCodigo(str, Enum):
    ADMIN   = "ADMIN"
    STOCK   = "STOCK"
    PEDIDOS = "PEDIDOS"
    CLIENT  = "CLIENT"


class EstadoPedidoCodigo(str, Enum):
    PENDIENTE  = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREP    = "EN_PREP"
    ENTREGADO  = "ENTREGADO"
    CANCELADO  = "CANCELADO"


class FormaPagoCodigo(str, Enum):
    MERCADOPAGO   = "MERCADOPAGO"
    EFECTIVO      = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"


# ─── Dominio 1: Identidad & Acceso ───────────────────────────────────────────

class Rol(SQLModel, table=True):
    __tablename__ = "rol" # type: ignore
    codigo:      RolCodigo        = Field(primary_key=True, max_length=20)
    nombre:      str              = Field(unique=True, max_length=50)
    descripcion: Optional[str]    = Field(default=None, sa_column=Column(Text))
    usuarios_rol: List["UsuarioRol"] = Relationship(back_populates="rol")


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario" # type: ignore
    id:            Optional[int]  = Field(default=None, primary_key=True)
    nombre:        str            = Field(max_length=80)
    apellido:      str            = Field(max_length=80)
    email:         str            = Field(unique=True, max_length=254)
    celular:       Optional[str]  = Field(default=None, max_length=20)
    password_hash: str            = Field(max_length=60)
    activo:        bool           = Field(default=True)
    created_at:    datetime       = Field(default_factory=datetime.utcnow)
    updated_at:    datetime       = Field(default_factory=datetime.utcnow)
    deleted_at:    Optional[datetime] = Field(default=None)
    usuarios_rol: List["UsuarioRol"] = Relationship(
    back_populates="usuario",
    sa_relationship_kwargs={
        "foreign_keys": "[UsuarioRol.usuario_id]",
    },
)
    direcciones:   List["DireccionEntrega"]      = Relationship(back_populates="usuario")
    pedidos:       List["Pedido"]               = Relationship(back_populates="usuario")
    historial:     List["HistorialEstadoPedido"] = Relationship(back_populates="usuario")

    @property
    def roles(self) -> List[Rol]:
        return [ur.rol for ur in self.usuarios_rol if ur.rol is not None]


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"
    usuario_id:      int              = Field(foreign_key="usuario.id", primary_key=True)
    rol_codigo:      RolCodigo        = Field(foreign_key="rol.codigo", primary_key=True, max_length=20)
    asignado_por_id: Optional[int]    = Field(default=None, foreign_key="usuario.id")
    expires_at:      Optional[datetime] = Field(default=None)
    created_at:      datetime          = Field(default_factory=datetime.utcnow)
    usuario: Optional["Usuario"] = Relationship(
        back_populates="usuarios_rol",
        sa_relationship_kwargs={
            "foreign_keys": "UsuarioRol.usuario_id",
        },
    )
    rol: Optional[Rol] = Relationship(back_populates="usuarios_rol")


class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direccion_entrega" # type: ignore
    id:            Optional[int]  = Field(default=None, primary_key=True)
    usuario_id:    int            = Field(foreign_key="usuario.id")
    alias:         Optional[str]  = Field(default=None, max_length=50)
    linea1:        str            = Field(sa_column=Column(Text, nullable=False))
    linea2:        Optional[str]  = Field(default=None, sa_column=Column(Text))
    ciudad:        str            = Field(max_length=100)
    provincia:     Optional[str]  = Field(default=None, max_length=100)
    codigo_postal: Optional[str]  = Field(default=None, max_length=10)
    es_principal:  bool           = Field(default=False)
    created_at:    datetime       = Field(default_factory=datetime.utcnow)
    updated_at:    datetime       = Field(default_factory=datetime.utcnow)
    deleted_at:    Optional[datetime] = Field(default=None)
    usuario: Optional[Usuario] = Relationship(back_populates="direcciones")
    pedidos: List["Pedido"]    = Relationship(back_populates="direccion")


# ─── Dominio 2: Catálogo de Productos ────────────────────────────────────────

class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida" # type: ignore
    id:      Optional[int] = Field(default=None, primary_key=True)
    nombre:  str           = Field(unique=True, max_length=50)
    simbolo: str           = Field(unique=True, max_length=10)
    tipo:    str           = Field(max_length=20)
    created_at: datetime   = Field(default_factory=datetime.utcnow)
    productos:    List["Producto"]            = Relationship(back_populates="unidad_venta")
    ingredientes: List["ProductoIngrediente"] = Relationship(back_populates="unidad_medida")


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria" # type: ignore
    id:          Optional[int]  = Field(default=None, primary_key=True)
    parent_id:   Optional[int]  = Field(default=None, foreign_key="categoria.id")
    nombre:      str            = Field(unique=True, max_length=100)
    descripcion: Optional[str]  = Field(default=None, sa_column=Column(Text))
    imagen_url:  Optional[str]  = Field(default=None, sa_column=Column(Text))
    created_at:  datetime       = Field(default_factory=datetime.utcnow)
    updated_at:  datetime       = Field(default_factory=datetime.utcnow)
    deleted_at:  Optional[datetime] = Field(default=None)
    productos_categoria: List["ProductoCategoria"] = Relationship(back_populates="categoria")


class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingrediente" # type: ignore
    id:             Optional[int] = Field(default=None, primary_key=True)
    nombre:         str           = Field(unique=True, max_length=100)
    descripcion:    Optional[str] = Field(default=None, sa_column=Column(Text))
    stock_cantidad: int           = Field(default=0, ge=0)
    es_alergeno:    bool          = Field(default=False)
    created_at:     datetime      = Field(default_factory=datetime.utcnow)
    updated_at:     datetime      = Field(default_factory=datetime.utcnow)
    deleted_at:     Optional[datetime] = Field(default=None)


class Producto(SQLModel, table=True):
    __tablename__ = "producto" # type: ignore
    id:              Optional[int]       = Field(default=None, primary_key=True)
    unidad_venta_id: Optional[int]       = Field(default=None, foreign_key="unidad_medida.id")
    nombre:          str                 = Field(max_length=150)
    descripcion:     Optional[str]       = Field(default=None, sa_column=Column(Text))
    precio_base:     float               = Field(ge=0)
    imagenes_url:    Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    stock_cantidad:  int                 = Field(default=0, ge=0)
    disponible:      bool                = Field(default=True)
    created_at:      datetime            = Field(default_factory=datetime.utcnow)
    updated_at:      datetime            = Field(default_factory=datetime.utcnow)
    deleted_at:      Optional[datetime]  = Field(default=None)
    unidad_venta:          Optional[UnidadMedida]       = Relationship(back_populates="productos")
    productos_categoria:   List["ProductoCategoria"]    = Relationship(back_populates="producto")
    productos_ingrediente: List["ProductoIngrediente"]  = Relationship(back_populates="producto")
    detalles_pedido:       List["DetallePedido"]        = Relationship(back_populates="producto")


class ProductoCategoria(SQLModel, table=True):
    __tablename__ = "producto_categoria" # type: ignore
    producto_id:  int      = Field(foreign_key="producto.id", primary_key=True)
    categoria_id: int      = Field(foreign_key="categoria.id", primary_key=True)
    es_principal: bool     = Field(default=False)
    created_at:   datetime = Field(default_factory=datetime.utcnow)
    producto:  Optional[Producto]  = Relationship(back_populates="productos_categoria")
    categoria: Optional[Categoria] = Relationship(back_populates="productos_categoria")


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente" # type: ignore
    producto_id:      int   = Field(foreign_key="producto.id", primary_key=True)
    ingrediente_id:   int   = Field(foreign_key="ingrediente.id", primary_key=True)
    unidad_medida_id: int   = Field(foreign_key="unidad_medida.id")
    cantidad:         float = Field(gt=0)
    es_removible:     bool  = Field(default=False)
    producto:      Optional[Producto]      = Relationship(back_populates="productos_ingrediente")
    ingrediente:   Optional[Ingrediente]   = Relationship(back_populates="productos_ingrediente")
    unidad_medida: Optional[UnidadMedida]  = Relationship(back_populates="ingredientes")


# ─── Dominio 3: Ventas, Pagos & Trazabilidad ─────────────────────────────────

class FormaPago(SQLModel, table=True):
    __tablename__ = "forma_pago" # type: ignore
    codigo:      FormaPagoCodigo = Field(primary_key=True, max_length=20)
    descripcion: str             = Field(max_length=80)
    habilitado:  bool            = Field(default=True)
    pedidos: List["Pedido"] = Relationship(back_populates="forma_pago")


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido" # type: ignore
    codigo:      EstadoPedidoCodigo = Field(primary_key=True, max_length=20)
    descripcion: str                = Field(max_length=80)
    orden:       int
    es_terminal: bool               = Field(default=False)
    pedidos:         List["Pedido"]                = Relationship(back_populates="estado")
    historial_desde: List["HistorialEstadoPedido"] = Relationship(
        back_populates="estado_desde_obj",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_desde]"},
    )
    historial_hacia: List["HistorialEstadoPedido"] = Relationship(
        back_populates="estado_hacia_obj",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_hacia]"},
    )


class Pedido(SQLModel, table=True):
    __tablename__ = "pedido" # type: ignore
    id:                Optional[int]      = Field(default=None, primary_key=True)
    usuario_id:        int                = Field(foreign_key="usuario.id")
    direccion_id:      Optional[int]      = Field(default=None, foreign_key="direccion_entrega.id")
    estado_codigo:     EstadoPedidoCodigo = Field(foreign_key="estado_pedido.codigo", max_length=20)
    forma_pago_codigo: FormaPagoCodigo    = Field(foreign_key="forma_pago.codigo", max_length=20)
    subtotal:    float = Field(ge=0)
    descuento:   float = Field(default=0.00, ge=0)
    costo_envio: float = Field(default=50.00, ge=0)
    total:       float = Field(ge=0)
    notas:       Optional[str]      = Field(default=None, sa_column=Column(Text))
    created_at:  datetime           = Field(default_factory=datetime.utcnow)
    updated_at:  datetime           = Field(default_factory=datetime.utcnow)
    deleted_at:  Optional[datetime] = Field(default=None)
    usuario:    Optional[Usuario]          = Relationship(back_populates="pedidos")
    direccion:  Optional[DireccionEntrega] = Relationship(back_populates="pedidos")
    estado:     Optional[EstadoPedido]     = Relationship(back_populates="pedidos")
    forma_pago: Optional[FormaPago]        = Relationship(back_populates="pedidos")
    detalles:   List["DetallePedido"]      = Relationship(back_populates="pedido")
    historial:  List["HistorialEstadoPedido"] = Relationship(back_populates="pedido")
    pagos:      List["Pago"]               = Relationship(back_populates="pedido")


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido" # type: ignore
    pedido_id:   int = Field(foreign_key="pedido.id", primary_key=True)
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    cantidad:        int            = Field(ge=1)
    nombre_snapshot: str            = Field(max_length=200)
    precio_snapshot: float          = Field(ge=0)
    subtotal_snap:   float          = Field(ge=0)
    personalizacion: Optional[List[int]] = Field(
        default=None, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pedido:   Optional[Pedido]   = Relationship(back_populates="detalles")
    producto: Optional[Producto] = Relationship(back_populates="detalles_pedido")


class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido" # type: ignore
    id:           Optional[int]             = Field(default=None, primary_key=True)
    pedido_id:    int                       = Field(foreign_key="pedido.id")
    estado_desde: Optional[EstadoPedidoCodigo] = Field(
        default=None, foreign_key="estado_pedido.codigo", max_length=20
    )
    estado_hacia: EstadoPedidoCodigo        = Field(
        foreign_key="estado_pedido.codigo", max_length=20
    )
    usuario_id:   Optional[int]  = Field(default=None, foreign_key="usuario.id")
    motivo:       Optional[str]  = Field(default=None, sa_column=Column(Text))
    created_at:   datetime       = Field(default_factory=datetime.utcnow)
    pedido:           Optional[Pedido]        = Relationship(back_populates="historial")
    usuario:          Optional[Usuario]       = Relationship(back_populates="historial")
    estado_desde_obj: Optional[EstadoPedido]  = Relationship(
        back_populates="historial_desde",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_desde]"},
    )
    estado_hacia_obj: Optional[EstadoPedido]  = Relationship(
        back_populates="historial_hacia",
        sa_relationship_kwargs={"foreign_keys": "[HistorialEstadoPedido.estado_hacia]"},
    )


class Pago(SQLModel, table=True):
    __tablename__ = "pago" # type: ignore
    id:                 Optional[int] = Field(default=None, primary_key=True)
    pedido_id:          int           = Field(foreign_key="pedido.id")
    mp_payment_id:      Optional[int] = Field(default=None, unique=True)
    mp_status:          str           = Field(max_length=30)
    mp_status_detail:   Optional[str] = Field(default=None, max_length=100)
    external_reference: str           = Field(unique=True, max_length=100)
    idempotency_key:    str           = Field(unique=True, max_length=100)
    transaction_amount: float         = Field(ge=0)
    payment_method_id:  Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pedido: Optional[Pedido] = Relationship(back_populates="pagos")