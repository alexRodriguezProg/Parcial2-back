import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_session
import app.repositories.unit_of_work as uow_module
from app.models import (
    Rol, RolCodigo,
    EstadoPedido, EstadoPedidoCodigo,
    FormaPago, FormaPagoCodigo,
    UnidadMedida,
    Usuario, UsuarioRol,
    Categoria, Producto,
    Pedido, DetallePedido, HistorialEstadoPedido,
    Pago,
)
from app.core.security import hash_password

# ─── Engine SQLite en memoria ─────────────────────────────────────────────────

DATABASE_URL_TEST = "sqlite://"

engine_test = create_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_test():
    with Session(engine_test) as session:
        yield session


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Crea todas las tablas una vez por sesión de tests."""
    SQLModel.metadata.create_all(engine_test)
    original_engine = uow_module.engine
    uow_module.engine = engine_test
    yield
    uow_module.engine = original_engine
    SQLModel.metadata.drop_all(engine_test)


@pytest.fixture(autouse=True)
def override_session():
    """Sobreescribe la dependencia get_session en cada test."""
    app.dependency_overrides[get_session] = get_session_test
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Limpia el rate limit entre tests."""
    from app.core.rate_limit import _intentos
    _intentos.clear()
    yield
    _intentos.clear()

@pytest.fixture(scope="session")
def seed_data():
    """Inserta datos base necesarios para todos los tests."""
    with Session(engine_test) as session:
        roles = [
            Rol(codigo=RolCodigo.ADMIN,   nombre="Administrador",  descripcion="Admin"),
            Rol(codigo=RolCodigo.CLIENT,  nombre="Cliente",        descripcion="Cliente"),
            Rol(codigo=RolCodigo.PEDIDOS, nombre="Gestor Pedidos", descripcion="Pedidos"),
            Rol(codigo=RolCodigo.STOCK,   nombre="Gestor Stock",   descripcion="Stock"),
        ]
        for r in roles:
            session.add(r)

        estados = [
            EstadoPedido(codigo=EstadoPedidoCodigo.PENDIENTE,  descripcion="Pendiente",  orden=1, es_terminal=False),
            EstadoPedido(codigo=EstadoPedidoCodigo.CONFIRMADO, descripcion="Confirmado", orden=2, es_terminal=False),
            EstadoPedido(codigo=EstadoPedidoCodigo.EN_PREP,    descripcion="En prep",    orden=3, es_terminal=False),
            EstadoPedido(codigo=EstadoPedidoCodigo.ENTREGADO,  descripcion="Entregado",  orden=4, es_terminal=True),
            EstadoPedido(codigo=EstadoPedidoCodigo.CANCELADO,  descripcion="Cancelado",  orden=5, es_terminal=True),
        ]
        for e in estados:
            session.add(e)

        formas = [
            FormaPago(codigo=FormaPagoCodigo.MERCADOPAGO,   descripcion="MercadoPago",  habilitado=True),
            FormaPago(codigo=FormaPagoCodigo.EFECTIVO,      descripcion="Efectivo",      habilitado=True),
            FormaPago(codigo=FormaPagoCodigo.TRANSFERENCIA, descripcion="Transferencia", habilitado=True),
        ]
        for f in formas:
            session.add(f)

        session.add(UnidadMedida(nombre="pieza", simbolo="u", tipo="contable"))
        session.commit()
    return True


@pytest.fixture
def client(seed_data):
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def admin_token(client):
    """Registra un usuario ADMIN y devuelve su token."""
    # Registrar
    client.post("/api/v1/auth/register", json={
        "nombre": "Admin", "apellido": "Test",
        "email": "admin@test.com", "password": "Admin1234!",
    })
    # Promover a ADMIN directamente en la BD
    with Session(engine_test) as session:
        from sqlmodel import select
        usuario = session.exec(
            select(Usuario).where(Usuario.email == "admin@test.com")
        ).first()
        if usuario:
            # Cambiar rol de CLIENT a ADMIN
            ur = session.exec(
                select(UsuarioRol).where(UsuarioRol.usuario_id == usuario.id)
            ).first()
            if ur:
                ur.rol_codigo = RolCodigo.ADMIN
                session.add(ur)
                session.commit()

    r = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin1234!",
    })
    return r.json()["access_token"]


@pytest.fixture
def client_token(client):
    """Registra un usuario CLIENT y devuelve su token."""
    client.post("/api/v1/auth/register", json={
        "nombre": "Cliente", "apellido": "Test",
        "email": "cliente@test.com", "password": "Cliente1234!",
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "cliente@test.com",
        "password": "Cliente1234!",
    })
    return r.json()["access_token"]


@pytest.fixture
def producto_factory(seed_data):
    """Crea un producto con stock disponible y devuelve su id."""
    with Session(engine_test) as session:
        producto = Producto(
            nombre="Producto Test",
            precio_base=100.0,
            stock_cantidad=50,
            disponible=True,
        )
        session.add(producto)
        session.commit()
        session.refresh(producto)
        return producto.id


@pytest.fixture
def pedido_factory(client, client_token, producto_factory):
    """Crea un pedido en estado PENDIENTE y devuelve su id."""
    r = client.post(
        "/api/v1/pedidos/",
        json={
            "items": [{"producto_id": producto_factory, "cantidad": 1, "personalizacion": None}],
            "forma_pago_codigo": "EFECTIVO",
        },
        cookies={"access_token": client_token},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]