"""端到端冒烟脚本（TestClient 全链路 + 鉴权）。

用法（在项目根目录）：
    .venv\\Scripts\\python backend\\tests\\e2e_smoke.py             # 无鉴权模式
    .venv\\Scripts\\python backend\\tests\\e2e_smoke.py --token t   # 鉴权模式（Token=t）
"""
import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


def run(token: str | None) -> None:
    data_dir = Path(tempfile.mkdtemp(prefix="im-e2e-"))
    os.environ["INVOICEMASTER_DATA_DIR"] = str(data_dir)
    os.environ["INVOICEMASTER_STATIC_DIR"] = str(data_dir / "no-static")
    if token:
        os.environ["INVOICEMASTER_API_TOKEN"] = token
    else:
        os.environ.pop("INVOICEMASTER_API_TOKEN", None)

    from fastapi.testclient import TestClient

    from app.main import app

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    client = TestClient(app)

    with client:  # 触发 lifespan（建库/建目录）
        # 健康检查始终无需鉴权
        r = client.get("/api/health")
        assert r.status_code == 200, r.text

        # 未带 Token 时受保护接口应 401（仅鉴权模式）
        if token:
            r = client.get("/api/invoices")
            assert r.status_code == 401, r.status_code

        # 列表可访问
        r = client.get("/api/invoices", headers=headers)
        assert r.status_code == 200, r.text

        # 上传样本
        pdf = BACKEND_DIR.parent / "template" / "1.pdf"
        assert pdf.exists(), "缺少 template/1.pdf 样本"
        with open(pdf, "rb") as f:
            r = client.post(
                "/api/invoices/upload",
                files=[("files", ("1.pdf", f, "application/pdf"))],
                headers=headers,
            )
        assert r.status_code == 200, r.text
        results = r.json()["results"]
        assert results[0]["status"] == "success", results
        invoice_id = results[0]["invoice_id"]

        # 重复上传应报 duplicate 且清理临时文件
        with open(pdf, "rb") as f:
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


if __name__ == "__main__":
    token = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--token" else None
    run(token)
