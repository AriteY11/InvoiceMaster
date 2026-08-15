from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
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
    from .models import auth  # noqa: F401
    from .models import invoice  # noqa: F401
    from .models import invoice_item  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_columns()


def _migrate_columns() -> None:
    """轻量迁移：为旧库补充新增列（create_all 不会修改已有表）。"""
    existing = {c["name"] for c in inspect(engine).get_columns("invoices")}
    if "uploaded_by" not in existing:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN uploaded_by VARCHAR(64)"))
