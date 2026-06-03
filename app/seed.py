from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import (
    Rol, RolCodigo, EstadoPedido, EstadoPedidoCodigo,
    FormaPago, FormaPagoCodigo, Usuario, UsuarioRol,
    Categoria, Ingrediente, Producto,
)
from app.services.auth_service import hash_password


def seed_roles(session):
    for data in [
        {"nombre": "Administrador", "codigo": RolCodigo.ADMIN, "descripcion": "CRUD completo"},
        {"nombre": "Gestor de Stock", "codigo": RolCodigo.STOCK, "descripcion": "Stock y disponibilidad"},
        {"nombre": "Gestor de Pedidos", "codigo": RolCodigo.PEDIDOS, "descripcion": "Ver y avanzar pedidos"},
        {"nombre": "Cliente", "codigo": RolCodigo.CLIENT, "descripcion": "Tienda y pedidos propios"},
    ]:
        if not session.exec(select(Rol).where(Rol.codigo == data["codigo"])).first():
            session.add(Rol(**data))
            print(f"  ✓ Rol {data['codigo']}")
    session.flush()


def seed_estados(session):
    for data in [
        {"nombre": "Pendiente",      "codigo": EstadoPedidoCodigo.PENDIENTE},
        {"nombre": "Confirmado",     "codigo": EstadoPedidoCodigo.CONFIRMADO},
        {"nombre": "En Preparación", "codigo": EstadoPedidoCodigo.EN_PREP},
        {"nombre": "En Camino",      "codigo": EstadoPedidoCodigo.EN_CAMINO},
        {"nombre": "Entregado",      "codigo": EstadoPedidoCodigo.ENTREGADO},
        {"nombre": "Cancelado",      "codigo": EstadoPedidoCodigo.CANCELADO},
    ]:
        if not session.exec(select(EstadoPedido).where(EstadoPedido.codigo == data["codigo"])).first():
            session.add(EstadoPedido(**data))
            print(f"  ✓ Estado {data['codigo']}")
    session.flush()


def seed_formas_pago(session):
    for data in [
        {"nombre": "Efectivo",       "codigo": FormaPagoCodigo.EFECTIVO},
        {"nombre": "Tarjeta",        "codigo": FormaPagoCodigo.TARJETA},
        {"nombre": "Transferencia",  "codigo": FormaPagoCodigo.TRANSFERENCIA},
        {"nombre": "MercadoPago",    "codigo": FormaPagoCodigo.MERCADOPAGO},
    ]:
        if not session.exec(select(FormaPago).where(FormaPago.codigo == data["codigo"])).first():
            session.add(FormaPago(**data))
            print(f"  ✓ FormaPago {data['codigo']}")
    session.flush()


def seed_admin(session):
    if not session.exec(select(Usuario).where(Usuario.email == "admin@parcial2.com")).first():
        admin = Usuario(nombre="Admin", apellido="Sistema", email="admin@parcial2.com",
                        password_hash=hash_password("Admin1234!"), activo=True)
        session.add(admin)
        session.flush()
        rol = session.exec(select(Rol).where(Rol.codigo == RolCodigo.ADMIN)).first()
        if rol:
            session.add(UsuarioRol(usuario_id=admin.id, rol_id=rol.id))
        print("  ✓ admin@parcial2.com / Admin1234!")
    session.flush()


def seed_categorias(session):
    cats = {}
    for data in [
        {"nombre": "Hamburguesas", "descripcion": "Hamburguesas artesanales"},
        {"nombre": "Pizzas",       "descripcion": "Pizzas al horno de piedra"},
        {"nombre": "Bebidas",      "descripcion": "Bebidas frías y calientes"},
        {"nombre": "Postres",      "descripcion": "Postres y dulces"},
    ]:
        existing = session.exec(select(Categoria).where(Categoria.nombre == data["nombre"])).first()
        if not existing:
            cat = Categoria(**data)
            session.add(cat)
            session.flush()
            cats[data["nombre"]] = cat.id
            print(f"  ✓ Categoría {data['nombre']}")
        else:
            cats[data["nombre"]] = existing.id
    for nombre, parent in [("Clásicas", "Hamburguesas"), ("Gourmet", "Hamburguesas"), ("Gaseosas", "Bebidas"), ("Jugos", "Bebidas")]:
        parent_id = cats.get(parent)
        if parent_id and not session.exec(select(Categoria).where(Categoria.nombre == nombre, Categoria.parent_id == parent_id)).first():
            session.add(Categoria(nombre=nombre, parent_id=parent_id))
            print(f"  ✓ Subcategoría {nombre}")
    session.flush()


def seed_ingredientes(session):
    for data in [
        {"nombre": "Pan brioche",           "es_alergeno": True},
        {"nombre": "Carne 200g",            "es_alergeno": False},
        {"nombre": "Queso cheddar",         "es_alergeno": True},
        {"nombre": "Lechuga",               "es_alergeno": False},
        {"nombre": "Tomate",                "es_alergeno": False},
        {"nombre": "Cebolla caramelizada",  "es_alergeno": False},
        {"nombre": "Mayonesa",              "es_alergeno": True},
        {"nombre": "Mostaza",               "es_alergeno": False},
    ]:
        if not session.exec(select(Ingrediente).where(Ingrediente.nombre == data["nombre"])).first():
            session.add(Ingrediente(**data))
            print(f"  ✓ Ingrediente {data['nombre']}")
    session.flush()


def seed_productos(session):
    cat_h = session.exec(select(Categoria).where(Categoria.nombre == "Hamburguesas")).first()
    cat_p = session.exec(select(Categoria).where(Categoria.nombre == "Pizzas")).first()
    cat_b = session.exec(select(Categoria).where(Categoria.nombre == "Bebidas")).first()
    for data in [
        {"nombre": "Hamburguesa Clásica", "descripcion": "Carne, lechuga, tomate y queso", "precio": 1500.0, "stock_cantidad": 50, "categoria_id": cat_h.id if cat_h else None, "imagen_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400"},
        {"nombre": "Hamburguesa BBQ",     "descripcion": "Doble carne y salsa BBQ",         "precio": 2000.0, "stock_cantidad": 30, "categoria_id": cat_h.id if cat_h else None, "imagen_url": "https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400"},
        {"nombre": "Pizza Margherita",    "descripcion": "Tomate, mozzarella y albahaca",   "precio": 1800.0, "stock_cantidad": 20, "categoria_id": cat_p.id if cat_p else None, "imagen_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400"},
        {"nombre": "Coca-Cola 500ml",     "descripcion": "Bebida gaseosa fría",             "precio":  500.0, "stock_cantidad": 100,"categoria_id": cat_b.id if cat_b else None, "imagen_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400"},
    ]:
        if not session.exec(select(Producto).where(Producto.nombre == data["nombre"])).first():
            session.add(Producto(**data))
            print(f"  ✓ Producto {data['nombre']}")
    session.flush()


def run_seed():
    print("\n🌱 Ejecutando seed...")
    create_db_and_tables()
    with Session(engine) as session:
        print("\n📋 Roles:");         seed_roles(session)
        print("\n📦 Estados:");       seed_estados(session)
        print("\n💳 Formas de pago:"); seed_formas_pago(session)
        print("\n👤 Admin:");         seed_admin(session)
        print("\n🗂️ Categorías:");    seed_categorias(session)
        print("\n🥬 Ingredientes:");  seed_ingredientes(session)
        print("\n🍔 Productos:");     seed_productos(session)
        session.commit()
    print("\n✅ Seed completado!\n")
    print("  Admin: admin@parcial2.com / Admin1234!")


if __name__ == "__main__":
    run_seed()