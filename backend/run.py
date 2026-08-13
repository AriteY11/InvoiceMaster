import sys
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from app.config import settings
from uvicorn import run

run("app.main:app", host=settings.host, port=settings.port)
