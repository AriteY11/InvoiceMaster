"""打印项目当前版本号（供构建脚本/CI 使用，单一数据源为 backend/app/config.py）。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "backend" / "app" / "config.py"

_PATTERN = re.compile(r'app_version: str = "([^"]+)"')


def get_version() -> str:
    text = CONFIG_PATH.read_text(encoding="utf-8")
    match = _PATTERN.search(text)
    if not match:
        raise RuntimeError(f"未在 {CONFIG_PATH} 中找到 app_version")
    return match.group(1)


if __name__ == "__main__":
    print(get_version())
