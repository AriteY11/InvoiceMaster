import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    info = sys.version_info
except Exception:
    print("[ERROR] Python version check failed.")
    input("Press Enter to exit...")
    sys.exit(1)

if info.major < 3 or (info.major == 3 and info.minor < 10):
    print("[ERROR] Python 3.10+ required. Current: {}.{}.{}".format(info.major, info.minor, info.micro))
    print("Download: https://www.python.org/downloads/")
    input("Press Enter to exit...")
    sys.exit(1)

VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
if not VENDOR_DIR.exists():
    print("[ERROR] Vendor dependencies not found at: {}".format(VENDOR_DIR))
    print("Please run: pip install --target vendor -r requirements.txt")
    input("Press Enter to exit...")
    sys.exit(1)

sys.path.insert(0, str(VENDOR_DIR))

SERVER_PROG = Path(__file__).resolve().parent / "run.py"
PYTHONW = Path(sys.exec_prefix) / "pythonw.exe"

server = subprocess.Popen(
    [str(PYTHONW), str(SERVER_PROG)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW,
)

URL = "http://127.0.0.1:8000/api/health"

for _ in range(30):
    time.sleep(1)
    try:
        req = urllib.request.urlopen(URL, timeout=2)
        if req.status == 200:
            subprocess.Popen(
                ["cmd", "/c", "start", "http://127.0.0.1:8000"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            break
    except Exception:
        pass

server.wait()
