from contextlib import contextmanager
from sqlmodel import Session
from app.database import engine


class UnitOfWork:
    def __init__(self):
        self.session: Session = None

    def __enter__(self):
        self.session = Session(engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
        return False


@contextmanager
def get_uow():
    uow = UnitOfWork()
    with uow:
        yield uow