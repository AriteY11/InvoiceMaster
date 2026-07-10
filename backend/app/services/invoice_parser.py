from __future__ import annotations

import re
from decimal import Decimal

from . import parser_rules as rules
from .pdf_extractor import ExtractionResult
from .text_normalizer import (
    normalize_fullwidth,
    normalize_text,
    parse_amount,
    parse_date,
    parse_tax_rate,
)


def _extract_value_after_keyword(text: str, field_key: str) -> str | None:
    keywords = rules.KEYWORD_MAP.get(field_key, [field_key])
    for line in text.split("\n"):
        normalized = rules.normalize_keyword(line)
        for kw in keywords:
            kw_norm = rules.normalize_keyword(kw)
            idx = normalized.find(kw_norm)
            if idx >= 0:
                after = normalized[idx + len(kw_norm):].strip()
                after = after.lstrip(":：").strip()
                if after:
                    return after
    return None


def _extract_invoice_name(text: str, pages: list) -> str | None:
    for pattern in rules.INVOICE_NAME_PATTERNS:
        if pattern in text:
            return pattern
    first_page_text = pages[0].text if pages else text
    first_line = first_page_text.strip().split("\n")[0] if first_page_text else ""
    if first_line and len(first_line) <= 50:
        return normalize_text(first_line)
    return None


def _extract_invoice_number_raw(text: str) -> str | None:
    raw = _extract_value_after_keyword(text, "invoice_number")
    if not raw:
        return None
    cleaned = re.sub(r"\s+", " ", raw).strip()
    return cleaned


def _extract_chinese_amount(text: str) -> str | None:
    for line in text.split("\n"):
        if "大写" in line or "价税合计" in line:
            m = re.search(r"([壹贰叁肆伍陆柒捌玖拾佰仟万亿元角分整零圆]+)", line)
            if m:
                return m.group(1)
    return None


def _parse_party_from_table(table_rows: list[list[str | None]]) -> tuple[dict, dict]:
    buyer: dict[str, str | None] = {"name": None, "tax_number": None}
    seller: dict[str, str | None] = {"name": None, "tax_number": None}

    for row in table_rows:
        if len(row) < 5:
            continue
        buyer_col = row[1]
        seller_col = row[4]

        if buyer_col and ("名称" in str(buyer_col) or "统一社会信用代码" in str(buyer_col)):
            buyer_cell = str(buyer_col)
            for part in buyer_cell.split("\n"):
                part = part.strip()
                if "名称" in part:
                    m = re.search(r"名称[：:]\s*(.+)", part)
                    if m:
                        buyer["name"] = m.group(1).strip()
                if "统一社会信用代码" in part:
                    m = re.search(r"统一社会信用代码[^\d]*([A-Za-z0-9]+)", part)
                    if m:
                        buyer["tax_number"] = m.group(1).strip()

        if seller_col and ("名称" in str(seller_col) or "统一社会信用代码" in str(seller_col)):
            seller_cell = str(seller_col)
            for part in seller_cell.split("\n"):
                part = part.strip()
                if "名称" in part:
                    m = re.search(r"名称[：:]\s*(.+)", part)
                    if m:
                        seller["name"] = m.group(1).strip()
                if "统一社会信用代码" in part:
                    m = re.search(r"统一社会信用代码[^\d]*([A-Za-z0-9]+)", part)
                    if m:
                        seller["tax_number"] = m.group(1).strip()

        if buyer["name"] and buyer["tax_number"] and seller["name"] and seller["tax_number"]:
            break

    return buyer, seller


def _extract_items_from_table_rows(table_rows: list[list[str | None]]) -> list[dict]:
    items: list[dict] = []

    PATTERN_WITH_QTY = re.compile(
        r"\*([^*]+)\*\s*(\S+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+(\d+\.?\d*)%\s+([\d.]+)"
    )
    PATTERN_NO_QTY = re.compile(
        r"\*([^*]+)\*\s*(\S+)\s+([\d.]+)\s+([\d.]+)\s+(\d+\.?\d*)%\s+([\d.]+)"
    )

    for row in table_rows:
        if len(row) < 1:
            continue
        cell_text = str(row[0]) if row[0] else ""

        if not any(name in cell_text for name in ["项目名称", "合 计", "行项目"]):
            continue

        combined = cell_text.replace("\n", " ").replace("  ", " ")

        m = PATTERN_WITH_QTY.search(combined)
        if m:
            items.append({
                "line_no": 1,
                "item_name": f"*{m.group(1)}*{m.group(2).strip()}",
                "specification": None,
                "unit": None,
                "quantity": parse_amount(m.group(4)),
                "unit_price": parse_amount(m.group(3)),
                "amount": parse_amount(m.group(5)),
                "tax_rate": parse_tax_rate(m.group(6)),
                "tax_amount": parse_amount(m.group(7)),
            })
            continue

        m = PATTERN_NO_QTY.search(combined)
        if m:
            raw_unit_price = parse_amount(m.group(3))
            raw_amount = parse_amount(m.group(4))
            quantity = None
            unit_price = raw_unit_price

            if (
                raw_unit_price is not None
                and raw_amount is not None
                and raw_amount > 0
                and raw_unit_price > raw_amount * 3
                and raw_unit_price > 1000
            ):
                integer_part = int(raw_unit_price)
                fraction_part = raw_unit_price - integer_part
                if integer_part >= 100:
                    possible_qty = integer_part // 1000
                    remaining = integer_part % 1000
                    possible_up = Decimal(str(remaining)) + fraction_part
                    if possible_qty >= 1 and abs(float(possible_up) - float(raw_amount)) < 1:
                        quantity = Decimal(str(possible_qty))
                        unit_price = possible_up

            items.append({
                "line_no": 1,
                "item_name": f"*{m.group(1)}*{m.group(2).strip()}",
                "specification": None,
                "unit": None,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": raw_amount,
                "tax_rate": parse_tax_rate(m.group(5)),
                "tax_amount": parse_amount(m.group(6)),
            })
            continue

        for line in cell_text.split("\n"):
            line_norm = normalize_text(line)
            if not ("*" in line_norm and "%" in line_norm):
                continue

            m = PATTERN_WITH_QTY.search(line_norm)
            has_qty = True
            if not m:
                m = PATTERN_NO_QTY.search(line_norm)
                has_qty = False

            if m:
                if has_qty:
                    items.append({
                        "line_no": len(items) + 1,
                        "item_name": f"*{m.group(1)}*{m.group(2).strip()}",
                        "specification": None,
                        "unit": None,
                        "quantity": parse_amount(m.group(4)),
                        "unit_price": parse_amount(m.group(3)),
                        "amount": parse_amount(m.group(5)),
                        "tax_rate": parse_tax_rate(m.group(6)),
                        "tax_amount": parse_amount(m.group(7)),
                    })
                else:
                    raw_up = parse_amount(m.group(3))
                    raw_am = parse_amount(m.group(4))
                    qty = None
                    up = raw_up
                    if (
                        raw_up is not None
                        and raw_am is not None
                        and raw_am > 0
                        and raw_up > raw_am * 3
                        and raw_up > 1000
                    ):
                        ip = int(raw_up)
                        fp = raw_up - ip
                        if ip >= 100:
                            pq = ip // 1000
                            rm = ip % 1000
                            pup = Decimal(str(rm)) + fp
                            if pq >= 1 and abs(float(pup) - float(raw_am)) < 1:
                                qty = Decimal(str(pq))
                                up = pup
                    items.append({
                        "line_no": len(items) + 1,
                        "item_name": f"*{m.group(1)}*{m.group(2).strip()}",
                        "specification": None,
                        "unit": None,
                        "quantity": qty,
                        "unit_price": up,
                        "amount": raw_am,
                        "tax_rate": parse_tax_rate(m.group(5)),
                        "tax_amount": parse_amount(m.group(6)),
                    })

        if items:
            break

    return items


def _extract_amounts_from_table(table_rows: list[list[str | None]]) -> tuple[Decimal | None, Decimal | None]:
    for row in table_rows:
        if len(row) < 3:
            continue
        cell = str(row[2]) if row[2] else ""
        if "小写" in cell:
            amounts = re.findall(r"¥\s*([\d,]+\.?\d{1,2})", normalize_fullwidth(cell))
            if amounts:
                total = parse_amount(amounts[0])
                return total, None

        if len(row) >= 1:
            col0 = str(row[0]) if row[0] else ""
            if "合 计" in col0:
                amounts = re.findall(r"¥\s*([\d,]+\.?\d{1,2})", col0)
                if len(amounts) >= 2:
                    return parse_amount(amounts[0]), parse_amount(amounts[1])
                if len(amounts) == 1:
                    return parse_amount(amounts[0]), None

    return None, None


def _extract_total_from_table(table_rows: list[list[str | None]]) -> Decimal | None:
    for row in table_rows:
        if len(row) >= 3:
            cell = str(row[2]) if row[2] else ""
            if "小写" in cell:
                amounts = re.findall(r"¥\s*([\d,]+\.?\d{1,2})", normalize_fullwidth(cell))
                if amounts:
                    return parse_amount(amounts[0])

        if len(row) >= 1:
            col0 = str(row[0]) if row[0] else ""
            if "合 计" in col0:
                amounts = re.findall(r"¥\s*([\d,]+\.?\d{1,2})", col0)
                parsed = [parse_amount(a) for a in amounts if parse_amount(a) and parse_amount(a) > 0]
                if len(parsed) >= 2:
                    return parsed[0] + parsed[1]
                if len(parsed) == 1:
                    return parsed[0]

    return None


def _compute_confidence(invoice_data: dict, items: list[dict]) -> float:
    total_fields = rules.EXPECTED_HEADER_FIELDS
    field_count = 0

    check_fields = [
        "invoice_name", "invoice_code", "invoice_number", "issue_date",
        "buyer_name", "buyer_tax_number",
        "seller_name", "seller_tax_number",
        "amount_excluding_tax", "tax_amount", "total_amount",
        "total_amount_text",
    ]

    for field in check_fields:
        val = invoice_data.get(field)
        if val is not None and val != "" and val != Decimal("0"):
            field_count += 1

    if items:
        field_count += min(len(items), 3)

    return min(round(field_count / total_fields, 2), 1.0)


def parse_invoice(extraction: ExtractionResult) -> dict:
    invoice_data: dict = {}
    warnings: list[str] = []
    text = extraction.raw_text

    invoice_data["invoice_name"] = _extract_invoice_name(extraction.raw_text, extraction.pages)

    invoice_data["invoice_number"] = _extract_invoice_number_raw(text)
    invoice_data["invoice_code"] = None

    date_raw = _extract_value_after_keyword(text, "issue_date")
    invoice_data["issue_date"] = parse_date(date_raw) if date_raw else None
    invoice_data["check_code"] = None
    invoice_data["machine_number"] = None

    all_tables: list[list[list[str | None]]] = []
    for page in extraction.pages:
        for table in page.tables:
            if table:
                all_tables.append(table)

    buyer_info: dict[str, str | None] = {"name": None, "tax_number": None}
    seller_info: dict[str, str | None] = {"name": None, "tax_number": None}
    items: list[dict] = []
    table_amount_without_tax = None
    table_tax_amount = None
    table_total_amount = None

    if all_tables:
        primary_table = all_tables[0]

        buyer_info, seller_info = _parse_party_from_table(primary_table)
        items = _extract_items_from_table_rows(primary_table)
        table_amount_without_tax, table_tax_amount = _extract_amounts_from_table(primary_table)
        table_total_amount = _extract_total_from_table(primary_table)

    if buyer_info["name"]:
        invoice_data["buyer_name"] = buyer_info["name"]
    else:
        buyer_name_raw = _extract_value_after_keyword(text, "buyer_name")
        invoice_data["buyer_name"] = buyer_name_raw

    invoice_data["buyer_tax_number"] = buyer_info["tax_number"]

    if seller_info["name"]:
        invoice_data["seller_name"] = seller_info["name"]
    else:
        seller_name_raw = _extract_value_after_keyword(text, "seller_name")
        invoice_data["seller_name"] = seller_name_raw

    invoice_data["seller_tax_number"] = seller_info["tax_number"]

    invoice_data["buyer_address_phone"] = None
    invoice_data["buyer_bank_account"] = None
    invoice_data["seller_address_phone"] = None
    invoice_data["seller_bank_account"] = None

    if table_total_amount:
        invoice_data["total_amount"] = table_total_amount
    else:
        for line in text.split("\n"):
            if "小写" in line:
                amounts = re.findall(r"¥\s*([\d,]+\.?\d{1,2})", line)
                if amounts:
                    invoice_data["total_amount"] = parse_amount(amounts[0])

    invoice_data["amount_excluding_tax"] = table_amount_without_tax
    invoice_data["tax_amount"] = table_tax_amount

    if invoice_data["total_amount"] and invoice_data["tax_amount"] and not invoice_data["amount_excluding_tax"]:
        invoice_data["amount_excluding_tax"] = invoice_data["total_amount"] - invoice_data["tax_amount"]
    elif invoice_data["total_amount"] and invoice_data["amount_excluding_tax"] and not invoice_data["tax_amount"]:
        invoice_data["tax_amount"] = invoice_data["total_amount"] - invoice_data["amount_excluding_tax"]
    elif invoice_data["amount_excluding_tax"] and invoice_data["tax_amount"] and not invoice_data["total_amount"]:
        invoice_data["total_amount"] = invoice_data["amount_excluding_tax"] + invoice_data["tax_amount"]

    invoice_data["total_amount_text"] = _extract_chinese_amount(text)
    invoice_data["remarks"] = _extract_value_after_keyword(text, "remarks")

    type_raw = _extract_value_after_keyword(text, "invoice_type")
    if not type_raw and invoice_data["invoice_name"]:
        type_raw = invoice_data["invoice_name"]
    invoice_data["invoice_type"] = type_raw

    if not items:
        warnings.append("未提取到行项目明细")

    for field_name in ["invoice_number", "issue_date", "buyer_name", "seller_name", "total_amount"]:
        if invoice_data.get(field_name) is None:
            warnings.append(f"未提取到字段: {field_name}")

    invoice_data["currency"] = "CNY"
    invoice_data["parser_warnings"] = warnings
    invoice_data["parse_confidence"] = _compute_confidence(invoice_data, items)
    invoice_data["items"] = items
    invoice_data["raw_text"] = text
    invoice_data["page_count"] = extraction.page_count

    return invoice_data
