import sys
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

from uvicorn import run
run("app.main:app", host="127.0.0.1", port=8000)
