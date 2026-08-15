"""模板 PDF 端到端解析回归测试。

样本位于项目根目录 template/（.gitignore 忽略，不随仓库分发）。
样本可由 git 历史恢复：git restore --source=a5daf92^ -- template/
"""
from pathlib import Path

import pytest

from app.services.invoice_parser import parse_invoice
from app.services.pdf_extractor import extract_pdf

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "template"

REQUIRED_FIELDS = [
    "invoice_name",
    "invoice_number",
    "issue_date",
    "seller_name",
    "total_amount",
]

# 已知样本的精确期望值（防止解析回归）
EXPECTED = {
    "1.pdf": {
        "invoice_number": "26127000000339320779",
        "seller_name": "天津海豚出游科技有限公司",
        "total_amount": "800.00",
        "amount_excluding_tax": "776.70",
        "tax_amount": "23.30",
    },
    "携程酒店订单电子发票（订单尾号4663）.pdf": {
        "invoice_number": "26317000002512937862",
        "seller_name": "上海赫程国际旅行社有限公司",
        "total_amount": "194.00",
        "seller_bank_account": "50131000551708444",
    },
    "携程酒店订单电子发票（订单尾号8383）.pdf": {
        "invoice_number": "26317000002512937921",
        "seller_name": "上海赫程国际旅行社有限公司",
        "total_amount": "355.54",
    },
}


def test_template_pdfs_parse():
    pdf_files = sorted(TEMPLATE_DIR.glob("*.pdf"))
    if not pdf_files:
        pytest.skip("template/ 样本 PDF 不存在")

    for pdf_path in pdf_files:
        extraction = extract_pdf(pdf_path)
        data = parse_invoice(extraction)

        for field in REQUIRED_FIELDS:
            assert data.get(field) is not None, f"{pdf_path.name} 缺少字段 {field}"
        assert data.get("items"), f"{pdf_path.name} 未提取到行项目"
        assert data.get("parse_confidence", 0) > 0, f"{pdf_path.name} 置信度为 0"

        expected = EXPECTED.get(pdf_path.name, {})
        for field, value in expected.items():
            actual = data.get(field)
            actual_str = str(actual) if actual is not None else None
            assert actual_str == value, f"{pdf_path.name} 字段 {field}: 期望 {value}，实际 {actual_str}"

        print(f"\n=== {pdf_path.name} ===")
        print(f"  发票号码: {data['invoice_number']}")
        print(f"  开票日期: {data['issue_date']}")
        print(f"  销售方: {data['seller_name']}")
        print(f"  价税合计: {data['total_amount']}")
        print(f"  行项目数: {len(data['items'])}")
        print(f"  置信度: {data['parse_confidence']:.0%}")
        print(f"  告警: {data['parser_warnings']}")
