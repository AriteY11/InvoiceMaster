from __future__ import annotations

import json
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


def _config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "InvoiceMaster"
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "InvoiceMaster"


CONFIG_FILE = _config_dir() / "online-config.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def save_config(data: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


def load_api_base() -> str:
    return str(load_config().get("api_base", ""))


def save_api_base(api_base: str) -> None:
    data = load_config()
    data["api_base"] = api_base.strip()
    save_config(data)


class Api:
    """通过 pywebview js_api 暴露给前端的接口。"""

    def get_api_base(self) -> str:
        return load_api_base()

    def save_api_base(self, api_base: str) -> None:
        save_api_base(api_base)

    def get_api_token(self) -> str:
        return str(load_config().get("api_token", ""))

    def save_api_token(self, api_token: str) -> None:
        data = load_config()
        data["api_token"] = api_token.strip()
        save_config(data)


def main() -> None:
    import webview

    index_html = _resource_path("frontend/dist-online") / "index.html"
    if not index_html.exists():
        print("[ERROR] 在线版前端未构建：请先运行 cd frontend && npm run build:online")
        sys.exit(1)

    api = Api()
    webview.create_window(
        "InvoiceMaster 发票管理（在线版）",
        str(index_html),
        js_api=api,
        width=1280,
        height=820,
        min_size=(1024, 700),
    )
    webview.start()


if __name__ == "__main__":
    main()
