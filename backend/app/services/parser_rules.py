from __future__ import annotations

import re

KEYWORD_MAP: dict[str, list[str]] = {
    "invoice_name": [
        "发票名称", "发票标题", "电子发票", "发票",
        "增值税电子普通发票", "增值税电子专用发票",
        "增值税普通发票", "增值税专用发票",
    ],
    "invoice_code": ["发票代码"],
    "invoice_number": ["发票号码", "发票号码：", "发票号码:"],
    "issue_date": ["开票日期"],
    "check_code": ["校验码"],
    "machine_number": ["机器编号"],
    "buyer_name": [
        "购买方 名称", "购买方名称", "购方名称",
        "购 名称", "名称",
    ],
    "buyer_tax_number": [
        "统一社会信用代码/纳税人识别号",
        "购买方纳税人识别号", "购方纳税人识别号",
        "纳税人识别号",
        "统一社会信用代码",
    ],
    "buyer_address_phone": [
        "购买方地址、电话", "购方地址、电话",
        "购买方地址", "购方地址", "地址、电话",
    ],
    "buyer_bank_account": [
        "购买方开户行及账号", "购方开户行及账号",
        "开户行及账号",
    ],
    "seller_name": [
        "销售方 名称", "销售方名称", "销方名称",
        "销 名称",
    ],
    "seller_tax_number": [
        "销售方纳税人识别号", "销方纳税人识别号",
    ],
    "seller_address_phone": [
        "销售方地址、电话", "销方地址、电话",
        "销售方地址", "销方地址",
    ],
    "seller_bank_account": [
        "销售方开户行及账号", "销方开户行及账号",
    ],
    "amount_excluding_tax": [
        "不含税金额", "金额（不含税）",
        "金额合计", "合计金额",
    ],
    "tax_amount": ["税额", "税 额", "税额合计", "税款"],
    "total_amount": [
        "价税合计", "合 计", "合计",
        "小写", "价税合计（小写）",
    ],
    "total_amount_text": ["大写", "价税合计（大写）", "大写合计"],
    "remarks": ["备注"],
    "invoice_type": ["发票类型", "发票种类"],
}

INVOICE_NAME_PATTERNS: list[str] = [
    "增值税电子普通发票",
    "增值税电子专用发票",
    "增值税普通发票",
    "增值税专用发票",
    "电子发票（普通发票）",
    "电子发票（增值税普通发票）",
    "电子发票（增值税专用发票）",
    "通用机打发票",
    "机动车销售统一发票",
]

TABLE_COLUMN_MAP: dict[str, list[str]] = {
    "item_name": [
        "货物或应税劳务、服务名称",
        "货物或应税劳务名称",
        "商品名称",
        "项目名称",
        "名称",
        "服务名称",
        "货物名称",
        "品名",
        "项目",
    ],
    "specification": ["规格型号", "规格", "型号"],
    "unit": ["单位", "计量单位"],
    "quantity": ["数量"],
    "unit_price": ["单价"],
    "amount": ["金额"],
    "tax_rate": ["税率", "征收率"],
    "tax_amount": ["税额"],
}

DATE_PATTERNS: list[str] = [
    r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
    r"(\d{4})-(\d{1,2})-(\d{1,2})",
    r"(\d{4})/(\d{1,2})/(\d{1,2})",
    r"(\d{4})\.(\d{1,2})\.(\d{1,2})",
]

INVOICE_CODE_PATTERN: str = r"(\d{10,12})"
INVOICE_NUMBER_PATTERN: str = r"(\d{8})"
TAX_NUMBER_PATTERN: str = r"([A-Za-z0-9]{15,20})"
AMOUNT_PATTERN: str = r"[￥¥]?\s*([\d,]+\.?\d*)"
TAX_RATE_PATTERN: str = r"(\d+\.?\d*)%"
CHINESE_AMOUNT_PATTERN: str = r"[壹贰叁肆伍陆柒捌玖拾佰仟万亿元角分整零]+"

EXPECTED_HEADER_FIELDS: int = 22


def normalize_keyword(text: str) -> str:
    return (
        text.replace("：", ":")
        .replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
        .replace("\u3000", "")
        .strip(":")
    )


def match_keyword(line: str, keywords: list[str]) -> bool:
    normalized = normalize_keyword(line)
    for kw in keywords:
        if normalize_keyword(kw) in normalized:
            return True
    return False


def find_column_index(headers: list[str | None], column_names: list[str]) -> int:
    for i, h in enumerate(headers):
        if h is None:
            continue
        cleaned = str(h).replace(" ", "").replace("\n", "")
        for col_name in column_names:
            if col_name.replace(" ", "") in cleaned:
                return i
    return -1
