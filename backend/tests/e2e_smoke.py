"""端到端冒烟脚本（TestClient 全链路 + 鉴权三模式）。

用法（在项目根目录）：
    .venv\\Scripts\\python backend\\tests\\e2e_smoke.py                  # 无鉴权（离线）模式
    .venv\\Scripts\\python backend\\tests\\e2e_smoke.py --token t        # 静态 Token 模式（Token=t）
    .venv\\Scripts\\python backend\\tests\\e2e_smoke.py --account        # 账号登录模式
"""
import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TEMPLATE_PDF = BACKEND_DIR.parent / "template" / "1.pdf"


def _prepare_env() -> Path:
    data_dir = Path(tempfile.mkdtemp(prefix="im-e2e-"))
    os.environ["INVOICEMASTER_DATA_DIR"] = str(data_dir)
    os.environ["INVOICEMASTER_STATIC_DIR"] = str(data_dir / "no-static")
    os.environ.pop("INVOICEMASTER_API_TOKEN", None)
    return data_dir


def _upload_sample(client, headers) -> int:
    assert TEMPLATE_PDF.exists(), "缺少 template/1.pdf 样本"
    with open(TEMPLATE_PDF, "rb") as f:
        r = client.post(
            "/api/invoices/upload",
            files=[("files", ("1.pdf", f, "application/pdf"))],
            headers=headers,
        )
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert results[0]["status"] == "success", results
    return results[0]["invoice_id"]


def run_token(token: str | None) -> None:
    """无鉴权（token=None）或静态 Token 模式。"""
    data_dir = _prepare_env()
    if token:
        os.environ["INVOICEMASTER_API_TOKEN"] = token

    from fastapi.testclient import TestClient

    from app.main import app

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    client = TestClient(app)

    with client:  # 触发 lifespan（建库/建目录）
        # 健康检查始终无需鉴权
        r = client.get("/api/health")
        assert r.status_code == 200, r.text

        # 未带 Token 时受保护接口应 401（仅静态 Token 模式）
        if token:
            r = client.get("/api/invoices")
            assert r.status_code == 401, r.status_code

        # 列表可访问
        r = client.get("/api/invoices", headers=headers)
        assert r.status_code == 200, r.text

        # 上传样本
        invoice_id = _upload_sample(client, headers)

        # 重复上传应报 duplicate 且清理临时文件
        with open(TEMPLATE_PDF, "rb") as f:
            r = client.post(
                "/api/invoices/upload",
                files=[("files", ("1.pdf", f, "application/pdf"))],
                headers=headers,
            )
        dup = r.json()["results"][0]
        assert dup["status"] == "duplicate", dup

        # 列表：解析字段正确
        body = client.get("/api/invoices", headers=headers).json()
        assert body["total"] == 1, body
        summary = body["items"][0]
        assert summary["invoice_number"] == "26127000000339320779", summary
        assert Decimal(str(summary["total_amount"])) == Decimal("800.00"), summary

        # 详情
        detail = client.get(f"/api/invoices/{invoice_id}", headers=headers).json()
        assert detail["items"], detail
        assert detail["seller_name"] == "天津海豚出游科技有限公司", detail
        assert Decimal(str(detail["amount_excluding_tax"])) == Decimal("776.70"), detail

        # 原 PDF 可下载
        r = client.get(f"/api/invoices/{invoice_id}/file", headers=headers)
        assert r.status_code == 200 and len(r.content) > 10000

        # 无临时文件残留
        leftovers = [p.name for p in (data_dir / "uploads").iterdir() if p.name.startswith(".tmp-")]
        assert not leftovers, leftovers

        # 删除后磁盘文件同步清理
        r = client.delete(f"/api/invoices/{invoice_id}", headers=headers)
        assert r.status_code == 200, r.text
        assert list((data_dir / "uploads").iterdir()) == []

    print(f"[token={'on' if token else 'off'}] E2E OK")


def run_account_mode() -> None:
    """账号登录模式：登录 → 上传记录上传人 → 上传人筛选 → 登出失效。"""
    data_dir = _prepare_env()

    from fastapi.testclient import TestClient

    from app.db import SessionLocal
    from app.main import app
    from app.models.auth import Account
    from app.services.auth import hash_password

    client = TestClient(app)

    with client:
        # 创建账号 alice / bob
        db = SessionLocal()
        db.add(Account(username="alice", password_hash=hash_password("secret123")))
        db.add(Account(username="bob", password_hash=hash_password("bobpass456")))
        db.commit()
        db.close()

        # 未登录访问受保护接口 → 401
        r = client.get("/api/invoices")
        assert r.status_code == 401, r.status_code

        # 错误密码 → 401
        r = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
        assert r.status_code == 401, r.status_code

        # 正确登录
        r = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["username"] == "alice" and body["token"]
        alice_headers = {"Authorization": f"Bearer {body['token']}"}

        # alice 上传 → uploaded_by = alice
        invoice_id = _upload_sample(client, alice_headers)
        summary = client.get("/api/invoices", headers=alice_headers).json()["items"][0]
        assert summary["uploaded_by"] == "alice", summary
        detail = client.get(f"/api/invoices/{invoice_id}", headers=alice_headers).json()
        assert detail["uploaded_by"] == "alice", detail

        # bob 登录后可见 alice 上传的发票（暂无权限区分）
        r = client.post("/api/auth/login", json={"username": "bob", "password": "bobpass456"})
        assert r.status_code == 200, r.text
        bob_headers = {"Authorization": f"Bearer {r.json()['token']}"}
        body = client.get("/api/invoices", headers=bob_headers).json()
        assert body["total"] == 1, body

        # 按上传人筛选
        body = client.get("/api/invoices", params={"uploader": "alice"}, headers=bob_headers).json()
        assert body["total"] == 1, body
        body = client.get("/api/invoices", params={"uploader": "bob"}, headers=bob_headers).json()
        assert body["total"] == 0, body

        # 手动录入也记录上传人
        r = client.post(
            "/api/invoices/manual",
            json=[{"invoice_name": "测试发票", "invoice_number": "M0001"}],
            headers=bob_headers,
        )
        assert r.status_code == 200, r.text
        body = client.get("/api/invoices", params={"uploader": "bob"}, headers=bob_headers).json()
        assert body["total"] == 1 and body["items"][0]["uploaded_by"] == "bob", body

        # 导出带上传人列
        r = client.get("/api/invoices/export", params={"format": "csv", "uploader": "alice"}, headers=bob_headers)
        assert r.status_code == 200
        csv_text = r.text
        assert "上传人" in csv_text and "alice" in csv_text

        # 登出后旧会话失效
        r = client.post("/api/auth/logout", headers=alice_headers)
        assert r.status_code == 200, r.text
        r = client.get("/api/invoices", headers=alice_headers)
        assert r.status_code == 401, r.status_code

    print("[account] E2E OK")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--token":
        run_token(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "--account":
        run_account_mode()
    else:
        run_token(None)
