from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.models import (
    Rol, RolCodigo,
    EstadoPedido, EstadoPedidoCodigo,
    FormaPago, FormaPagoCodigo,
    UnidadMedida,
    Usuario, UsuarioRol,
)
from app.core.security import hash_password


def seed_roles(session: Session):
    for data in [
        {"codigo": RolCodigo.ADMIN,   "nombre": "Administrador",     "descripcion": "Acceso total sin restricciones"},
        {"codigo": RolCodigo.STOCK,   "nombre": "Gestor de Stock",   "descripcion": "Actualiza stock y disponible"},
        {"codigo": RolCodigo.PEDIDOS, "nombre": "Gestor de Pedidos", "descripcion": "Avanza estados CONFIRMADO→ENTREGADO"},
        {"codigo": RolCodigo.CLIENT,  "nombre": "Cliente",           "descripcion": "Opera solo sus propios datos"},
    ]:
        if not session.exec(select(Rol).where(Rol.codigo == data["codigo"])).first():
            session.add(Rol(**data))
            print(f"  ✓ Rol {data['codigo']}")
    session.flush()


def seed_estados(session: Session):
    for data in [
        {"codigo": EstadoPedidoCodigo.PENDIENTE,  "descripcion": "Pedido creado, pago pendiente", "orden": 1, "es_terminal": False},
        {"codigo": EstadoPedidoCodigo.CONFIRMADO, "descripcion": "Pago procesado y confirmado",    "orden": 2, "es_terminal": False},
        {"codigo": EstadoPedidoCodigo.EN_PREP,    "descripcion": "En preparación en cocina",       "orden": 3, "es_terminal": False},
        {"codigo": EstadoPedidoCodigo.ENTREGADO,  "descripcion": "Entrega confirmada",             "orden": 4, "es_terminal": True},
        {"codigo": EstadoPedidoCodigo.CANCELADO,  "descripcion": "Pedido cancelado",               "orden": 5, "es_terminal": True},
    ]:
        if not session.exec(select(EstadoPedido).where(EstadoPedido.codigo == data["codigo"])).first():
            session.add(EstadoPedido(**data))
            print(f"  ✓ Estado {data['codigo']}")
    session.flush()


def seed_formas_pago(session: Session):
    for data in [
        {"codigo": FormaPagoCodigo.MERCADOPAGO,   "descripcion": "Checkout API · CardPayment SDK", "habilitado": True},
        {"codigo": FormaPagoCodigo.EFECTIVO,      "descripcion": "Retiro en local",                "habilitado": True},
        {"codigo": FormaPagoCodigo.TRANSFERENCIA, "descripcion": "Transferencia bancaria",         "habilitado": True},
    ]:
        if not session.exec(select(FormaPago).where(FormaPago.codigo == data["codigo"])).first():
            session.add(FormaPago(**data))
            print(f"  ✓ FormaPago {data['codigo']}")
    session.flush()


def seed_unidades_medida(session: Session):
    for data in [
        {"nombre": "kilogramo", "simbolo": "kg",  "tipo": "peso"},
        {"nombre": "gramo",     "simbolo": "g",   "tipo": "peso"},
        {"nombre": "litro",     "simbolo": "L",   "tipo": "volumen"},
        {"nombre": "mililitro", "simbolo": "mL",  "tipo": "volumen"},
        {"nombre": "pieza",     "simbolo": "u",   "tipo": "contable"},
        {"nombre": "docena",    "simbolo": "doc", "tipo": "contable"},
    ]:
        if not session.exec(select(UnidadMedida).where(UnidadMedida.simbolo == data["simbolo"])).first():
            session.add(UnidadMedida(**data))  # type: ignore
            print(f"  ✓ UnidadMedida {data['simbolo']}")
    session.flush()


def seed_admin(session: Session):
    if not session.exec(select(Usuario).where(Usuario.email == "admin@foodstore.com")).first():
        admin = Usuario(
            nombre="Admin", apellido="FoodStore",
            email="admin@foodstore.com",
            password_hash=hash_password("Admin1234!"),
            activo=True,
        )
        session.add(admin)
        session.flush()
        session.add(UsuarioRol(usuario_id=admin.id, rol_codigo=RolCodigo.ADMIN)) # type: ignore
        print("  ✓ admin@foodstore.com / Admin1234!")
    session.flush()


def run_seed():
    print("\n🌱 Ejecutando seed...")
    create_db_and_tables()
    with Session(engine) as session:
        print("\n📋 Roles:");           seed_roles(session)
        print("\n📦 Estados pedido:");  seed_estados(session)
        print("\n💳 Formas de pago:");  seed_formas_pago(session)
        print("\n📐 Unidades medida:"); seed_unidades_medida(session)
        print("\n👤 Admin:");           seed_admin(session)
        session.commit()
    print("\n✅ Seed completado!\n")
    print("  Admin: admin@foodstore.com / Admin1234!")


if __name__ == "__main__":
    run_seed()