#!/usr/bin/env python
"""InvoiceMaster 在线版账号管理脚本（随 release 交付，运行于后端所在机器）。

用法：
    python scripts/manage_accounts.py [数据目录]

交互式菜单：新增账号 / 修改已有账号密码 / 查看账号列表。
数据目录默认取环境变量 INVOICEMASTER_DATA_DIR（Linux 部署为 /var/lib/invoicemaster/data），
也可通过命令行参数指定。
"""
import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if len(sys.argv) > 1:
    import os

    os.environ["INVOICEMASTER_DATA_DIR"] = sys.argv[1]

from app.config import DATABASE_FILE, ensure_directories  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models.auth import Account  # noqa: E402
from app.services.auth import hash_password  # noqa: E402


def _input_username(prompt: str) -> str | None:
    name = input(prompt).strip()
    if not name:
        print("[错误] 账号名不能为空")
        return None
    if len(name) > 64:
        print("[错误] 账号名过长（最多 64 字符）")
        return None
    return name


def _read_password(prompt: str) -> str:
    """交互终端用 getpass 隐藏回显；管道/重定向（自动化）时回退为 input。"""
    try:
        if not sys.stdin.isatty():
            return input(prompt)
    except (AttributeError, ValueError):
        pass
    return getpass.getpass(prompt)


def _input_password() -> str | None:
    p1 = _read_password("  请输入密码（至少 6 位，输入不回显）: ").strip()
    if len(p1) < 6:
        print("[错误] 密码长度至少 6 位")
        return None
    p2 = _read_password("  请再次输入密码确认: ").strip()
    if p1 != p2:
        print("[错误] 两次输入的密码不一致")
        return None
    return p1


def add_account(db) -> None:
    username = _input_username("请输入要新增的账号名称: ")
    if username is None:
        return
    if db.query(Account).filter(Account.username == username).first():
        print(f"[错误] 账号 {username} 已存在，如需修改请选择“修改已有账号密码”")
        return
    password = _input_password()
    if password is None:
        return
    db.add(Account(username=username, password_hash=hash_password(password)))
    db.commit()
    print(f"[完成] 账号 {username} 已创建")


def change_password(db) -> None:
    username = _input_username("请输入要修改密码的账号名称: ")
    if username is None:
        return
    account = db.query(Account).filter(Account.username == username).first()
    if account is None:
        print(f"[错误] 账号 {username} 不存在")
        return
    password = _input_password()
    if password is None:
        return
    account.password_hash = hash_password(password)
    db.commit()
    print(f"[完成] 账号 {username} 的密码已更新")


def list_accounts(db) -> None:
    accounts = db.query(Account).order_by(Account.created_at).all()
    if not accounts:
        print("（暂无账号）")
        return
    for account in accounts:
        print(f"  - {account.username}（创建于 {account.created_at:%Y-%m-%d %H:%M}）")


def main() -> None:
    print("=" * 46)
    print("  InvoiceMaster 在线版账号管理")
    print(f"  数据文件：{DATABASE_FILE}")
    print("=" * 46)
    ensure_directories()
    init_db()
    db = SessionLocal()
    try:
        while True:
            print()
            print("  1. 新增账号")
            print("  2. 修改已有账号密码")
            print("  3. 查看账号列表")
            print("  0. 退出")
            choice = input("请选择操作: ").strip()
            if choice == "1":
                add_account(db)
            elif choice == "2":
                change_password(db)
            elif choice == "3":
                list_accounts(db)
            elif choice == "0":
                break
            else:
                print("[提示] 无效选项，请重新输入")
    finally:
        db.close()


if __name__ == "__main__":
    main()
