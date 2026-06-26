from contextlib import contextmanager
from sqlmodel import Session
from app.core.database import engine


class UnitOfWork:
    def __init__(self) -> None:
        """Inicializa el UoW sin sesión (se crea en __enter__)."""
        self.session: Session = None  # type: ignore

    def __enter__(self):
        """Crea una sesión y la deja disponible."""
        self.session = Session(engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit o rollback según si hubo excepción, y cierra la sesión."""
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


@contextmanager
def get_uow():
    """Context manager que envuelve UnitOfWork para inyección."""
    uow = UnitOfWork()
    with uow:
        yield uow