from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


def create_db_and_tables() -> None:
    """Crea todas las tablas en la BD si no existen."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Generador que yield una sesión de BD."""
    with Session(engine) as session:
        yield session