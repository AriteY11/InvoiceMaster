"""桌面版启动器（兼容旧入口）：启动离线版 pywebview 桌面应用。"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from desktop.offline_app import main

if __name__ == "__main__":
    main()
