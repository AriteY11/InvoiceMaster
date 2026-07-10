from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models.base import Base

engine = create_engine(
    settings.database_url,
    connect_args={'check_same_thread': False},
    echo=settings.sqlite_echo,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from .models import invoice  # noqa: F401
    from .models import invoice_item  # noqa: F401

    Base.metadata.create_all(bind=engine)
