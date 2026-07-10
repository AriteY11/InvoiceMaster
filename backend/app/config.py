from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / 'data'
UPLOAD_DIR = DATA_DIR / 'uploads'
STATIC_DIR = PROJECT_ROOT / 'frontend' / 'dist'
DATABASE_FILE = DATA_DIR / 'invoices.db'


@dataclass(frozen=True)
class Settings:
    app_name: str = 'InvoiceMaster API'
    app_version: str = '1.6.0'
    allowed_extensions: tuple[str, ...] = ('.pdf',)
    max_upload_size_mb: int = 20
    default_currency: str = 'CNY'
    sqlite_echo: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite:///{DATABASE_FILE.as_posix()}"


settings = Settings()


def ensure_directories() -> None:
    for path in (DATA_DIR, UPLOAD_DIR):
        path.mkdir(parents=True, exist_ok=True)
