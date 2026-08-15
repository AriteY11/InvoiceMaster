from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


def _default_data_dir() -> Path:
    """默认数据目录：优先环境变量，其次平台可移植位置。

    - Windows: %LOCALAPPDATA%/InvoiceMaster/data
    - Linux:   $XDG_DATA_HOME/InvoiceMaster/data 或 ~/.local/share/InvoiceMaster/data
    """
    env = os.environ.get("INVOICEMASTER_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "InvoiceMaster" / "data"
    xdg = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(xdg) / "InvoiceMaster" / "data"


DATA_DIR = _default_data_dir()
UPLOAD_DIR = DATA_DIR / "uploads"

_static_env = os.environ.get("INVOICEMASTER_STATIC_DIR")
STATIC_DIR = (
    Path(_static_env).expanduser().resolve()
    if _static_env
    else PROJECT_ROOT / "frontend" / "dist"
)

DATABASE_FILE = DATA_DIR / "invoices.db"


@dataclass(frozen=True)
class Settings:
    app_name: str = "InvoiceMaster API"
    app_version: str = "2.1.1"
    allowed_extensions: tuple[str, ...] = (".pdf",)
    max_upload_size_mb: int = 20
    default_currency: str = "CNY"
    sqlite_echo: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite:///{DATABASE_FILE.as_posix()}"

    @property
    def host(self) -> str:
        return os.environ.get("INVOICEMASTER_HOST", "127.0.0.1")

    @property
    def port(self) -> int:
        return int(os.environ.get("INVOICEMASTER_PORT", "8000"))

    @property
    def cors_origins(self) -> list[str]:
        raw = os.environ.get("INVOICEMASTER_CORS_ORIGINS", "*")
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def api_token(self) -> str | None:
        raw = os.environ.get("INVOICEMASTER_API_TOKEN", "").strip()
        return raw or None


settings = Settings()


def ensure_directories() -> None:
    for path in (DATA_DIR, UPLOAD_DIR):
        path.mkdir(parents=True, exist_ok=True)
