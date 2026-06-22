"""
Seed de datos de prueba: ingredientes, categorías y productos.
Correr con: PYTHONIOENCODING=utf-8 python -m app.seed_data
"""
from sqlmodel import Session, select
from app.core.database import engine
from app.models import (
    Ingrediente,
    Categoria,
    Producto,
    ProductoCategoria,
    ProductoIngrediente,
)


def seed_ingredientes(session: Session) -> dict[str, int]:
    """Crea ingredientes de prueba y devuelve {nombre: id}"""
    nombres = [
        "Medallón de Carne", "Lechuga", "Tomate", "Queso Cheddar",
        "Pan de Hamburguesa", "Cebolla", "Pepinillos", "Salsa Ketchup",
        "Salsa Mostaza", "Pollo Rebozado", "Papa", "Huevo", "Bacon",
        "Dulce de Leche", "Crema Chantilly",
    ]
    ids = {}
    for nombre in nombres:
        existente = session.exec(
            select(Ingrediente).where(Ingrediente.nombre == nombre)
        ).first()
        if existente:
            ids[nombre] = existente.id
        else:
            ing = Ingrediente(
                nombre=nombre,
                descripcion=f"Ingrediente: {nombre}",
                stock_cantidad=100,
                es_alergeno=nombre in ("Huevo", "Leche", "Crema Chantilly"),
            )
            session.add(ing)
            session.flush()
            ids[nombre] = ing.id
            print(f"  ✓ Ingrediente: {nombre}")
    return ids


def seed_categorias(session: Session) -> dict[str, int]:
    """Devuelve {nombre: id} de categorías existentes"""
    cats = session.exec(select(Categoria)).all()
    return {c.nombre: c.id for c in cats}


def seed_productos(session: Session, ing_ids: dict, cat_ids: dict):
    """Crea productos de prueba con sus categorías e ingredientes"""
    u = 5  # unidad_venta_id = "pieza" (u)

    productos_data = [
        {
            "nombre": "Hamburguesa Clásica",
            "descripcion": "Medallón de carne 150g con lechuga, tomate y cebolla en pan artesanal.",
            "precio_base": 5500.0,
            "categoria_id": cat_ids.get("Hamburguesas de Mc"),
            "ingredientes": [
                (ing_ids["Pan de Hamburguesa"], 1, u, False),
                (ing_ids["Medallón de Carne"], 1, u, False),
                (ing_ids["Lechuga"], 1, u, True),
                (ing_ids["Tomate"], 1, u, True),
                (ing_ids["Cebolla"], 1, u, True),
            ],
        },
        {
            "nombre": "Hamburguesa Cheddar",
            "descripcion": "Medallón de carne con doble capa de queso cheddar derretido y cebolla caramelizada.",
            "precio_base": 6500.0,
            "categoria_id": cat_ids.get("Hamburguesas de Mc"),
            "ingredientes": [
                (ing_ids["Pan de Hamburguesa"], 1, u, False),
                (ing_ids["Medallón de Carne"], 1, u, False),
                (ing_ids["Queso Cheddar"], 2, u, True),
                (ing_ids["Cebolla"], 1, u, True),
            ],
        },
        {
            "nombre": "Hamburguesa Bacon",
            "descripcion": "Medallón de carne con bacon crocante, queso cheddar y salsa especial.",
            "precio_base": 7200.0,
            "categoria_id": cat_ids.get("Hamburguesas de Mc"),
            "ingredientes": [
                (ing_ids["Pan de Hamburguesa"], 1, u, False),
                (ing_ids["Medallón de Carne"], 1, u, False),
                (ing_ids["Bacon"], 3, u, True),
                (ing_ids["Queso Cheddar"], 1, u, True),
                (ing_ids["Salsa Ketchup"], 1, u, True),
            ],
        },
        {
            "nombre": "Papas Fritas Grandes",
            "descripcion": "Porción grande de papas fritas golden crujientes con sal marina.",
            "precio_base": 2800.0,
            "categoria_id": cat_ids.get("Comidas Rápidas"),
            "ingredientes": [
                (ing_ids["Papa"], 1, u, False),
            ],
        },
        {
            "nombre": "Nuggets de Pollo (6u)",
            "descripcion": "6 nuggets de pollo rebozado, ideales para compartir.",
            "precio_base": 3500.0,
            "categoria_id": cat_ids.get("Comidas Rápidas"),
            "ingredientes": [
                (ing_ids["Pollo Rebozado"], 6, u, False),
            ],
        },
        {
            "nombre": "McFlurry de Dulce de Leche",
            "descripcion": "Helado cremoso con dulce de leche y copos de crema.",
            "precio_base": 3200.0,
            "categoria_id": cat_ids.get("Comidas Rápidas"),
            "ingredientes": [
                (ing_ids["Dulce de Leche"], 1, u, True),
                (ing_ids["Crema Chantilly"], 1, u, True),
            ],
        },
    ]

    for pd in productos_data:
        existente = session.exec(
            select(Producto).where(Producto.nombre == pd["nombre"])
        ).first()
        if existente:
            print(f"  ~ Producto ya existe: {pd['nombre']}")
            continue

        prod = Producto(
            nombre=pd["nombre"],
            descripcion=pd["descripcion"],
            precio_base=pd["precio_base"],
            stock_cantidad=50,
            disponible=True,
            unidad_venta_id=u,
        )
        session.add(prod)
        session.flush()

        # Asignar categoría
        session.add(ProductoCategoria(
            producto_id=prod.id,
            categoria_id=pd["categoria_id"],
            es_principal=True,
        ))

        # Asignar ingredientes
        for ing_id, cantidad, unidad_id, removible in pd["ingredientes"]:
            session.add(ProductoIngrediente(
                producto_id=prod.id,
                ingrediente_id=ing_id,
                cantidad=cantidad,
                unidad_medida_id=unidad_id,
                es_removible=removible,
            ))

        print(f"  ✓ Producto: {pd['nombre']} (${pd['precio_base']:,.0f})")

    session.flush()


def run():
    print("\n🌱 Sembrando datos de prueba...")
    with Session(engine) as session:
        print("\n🥗 Ingredientes:")
        ing_ids = seed_ingredientes(session)

        print("\n🗂️  Categorías:")
        cat_ids = seed_categorias(session)
        for nombre, id_ in cat_ids.items():
            print(f"  · {nombre} (id={id_})")

        print("\n🍔 Productos:")
        seed_productos(session, ing_ids, cat_ids)

        session.commit()
    print("\n✅ Datos de prueba listos!\n")


if __name__ == "__main__":
    run()
