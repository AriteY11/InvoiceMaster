from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _resource_path(relative: str) -> Path:
    """PyInstaller 打包后（sys._MEIPASS）与源码运行均能定位资源目录。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative
    return Path(__file__).resolve().parents[2] / relative


def main() -> None:
    # 静态目录必须在 import app（触发 config 求值）之前注入
    static_dir = _resource_path("frontend/dist")
    if static_dir.exists():
        os.environ["INVOICEMASTER_STATIC_DIR"] = str(static_dir)

    import webview

    from app.embedded import EmbeddedServer

    server = EmbeddedServer(port=0)
    url = server.start()
    if not server.wait_ready(timeout=20):
        print("[ERROR] 后端服务启动失败")
        sys.exit(1)

    webview.create_window(
        "InvoiceMaster 发票管理",
        url,
        width=1280,
        height=820,
        min_size=(1024, 700),
    )
    webview.start()
    server.stop()


if __name__ == "__main__":
    main()
