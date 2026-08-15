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

# 参与置信度计算的表头字段（currency 恒定，不参与；行项目单独加分）
_CONFIDENCE_FIELDS = [
    "invoice_name", "invoice_code", "invoice_number", "issue_date",
    "check_code", "machine_number", "invoice_type",
    "buyer_name", "buyer_tax_number", "buyer_address_phone", "buyer_bank_account",
    "seller_name", "seller_tax_number", "seller_address_phone", "seller_bank_account",
    "amount_excluding_tax", "tax_amount", "total_amount", "total_amount_text",
    "remarks",
]

_AMOUNT_TOKEN_RE = re.compile(r"¥\s*([\d,]+\.?\d{1,2})")


def _empty_party() -> dict[str, str | None]:
    return {"name": None, "tax_number": None, "address_phone": None, "bank_account": None}


def _merge_party(target: dict[str, str | None], block: dict[str, str | None]) -> None:
    for key, value in block.items():
        if value and target.get(key) is None:
            target[key] = value


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


def _extract_invoice_code(text: str) -> str | None:
    raw = _extract_value_after_keyword(text, "invoice_code")
    if raw:
        m = re.search(r"(\d{10,12})", raw)
        if m:
            return m.group(1)
    return None


def _extract_invoice_number(text: str) -> str | None:
    raw = _extract_value_after_keyword(text, "invoice_number")
    if raw:
        cleaned = re.sub(r"\s+", " ", raw).strip()
        m = re.search(r"(\d{8,20})", cleaned)
        if m:
            return m.group(1)
    return None


def _extract_check_code(text: str) -> str | None:
    raw = _extract_value_after_keyword(text, "check_code")
    if not raw:
        return None
    cleaned = re.sub(r"\s+", " ", raw).strip()
    if re.fullmatch(r"[\d\s]{10,40}", cleaned):
        return cleaned.replace(" ", "")
    return cleaned


def _extract_machine_number(text: str) -> str | None:
    raw = _extract_value_after_keyword(text, "machine_number")
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


# ---- 买卖方信息 ---- #

_LABEL_VALUE_RES: list[tuple[str, re.Pattern]] = [
    ("name", re.compile(r"^\s*名\s*称\s*[：:]\s*(.*)")),
    ("tax_number", re.compile(r"^\s*(?:统一社会信用代码\s*/\s*纳税人识别号|纳税人识别号|统一社会信用代码)[/：:]*\s*(.*)")),
    ("address_phone", re.compile(r"(?:地址、电话|地址电话|地址)\s*[：:]\s*(.*)")),
    ("bank_account", re.compile(r"(?:开户行及账号|开户行|账号)\s*[：:]\s*(.*)")),
]

_BUYER_MARKER_RE = re.compile(r"购买方|购方|购\s*买\s*方")
_SELLER_MARKER_RE = re.compile(r"销售方|销方|销\s*售\s*方")


def _parse_party_block(lines: list[str]) -> dict[str, str | None]:
    """从买卖方单元格/文本块中提取名称、税号、地址电话、开户行及账号。

    兼容“标签与值同行”和“标签行后换行跟值”两种排版。
    """
    result = _empty_party()
    pending_key: str | None = None
    for raw_line in lines:
        line = normalize_fullwidth(raw_line.strip())
        if not line:
            continue
        if pending_key:
            value = line.strip()
            if pending_key == "tax_number":
                m = re.search(r"([A-Za-z0-9]{15,20})", value)
                value = m.group(1) if m else value
            if result[pending_key] is None and value:
                result[pending_key] = value
            pending_key = None
            continue
        for key, pattern in _LABEL_VALUE_RES:
            m = pattern.search(line)
            if not m:
                continue
            value = m.group(1).strip()
            if value:
                if result[key] is None:
                    result[key] = value
            else:
                pending_key = key
            break
    return result


def _party_side(text: str) -> str | None:
    if _SELLER_MARKER_RE.search(text):
        return "seller"
    if _BUYER_MARKER_RE.search(text):
        return "buyer"
    return None


def _is_party_cell(text: str) -> bool:
    if re.search(r"统一社会信用代码|纳税人识别号", text):
        return True
    # 排除“公司开户银行名称”等非买卖方名称的“名称：”
    return bool(re.search(r"(?<!银行)名\s*称\s*[：:]", text))


def _parse_party_from_table(table_rows: list[list[str | None]]) -> tuple[dict, dict]:
    buyer = _empty_party()
    seller = _empty_party()

    for row in table_rows:
        for cell in row:
            if not cell:
                continue
            cell_text = str(cell)
            if not _is_party_cell(cell_text):
                continue
            block = _parse_party_block(cell_text.split("\n"))
            side = _party_side(cell_text)
            if side == "seller":
                _merge_party(seller, block)
            elif side == "buyer":
                _merge_party(buyer, block)
            elif buyer.get("name") is None:
                _merge_party(buyer, block)
            else:
                _merge_party(seller, block)

    return buyer, seller


_NOISE_PREFIX_RE = re.compile(r"^[\s购买卖方信销息售]*?(?=名|统一|纳税人|地址|开户|公司)")
_TAX_RUN_RE = re.compile(r"[A-Za-z0-9]{15,20}")
_INTERLEAVE_SPLIT_RE = re.compile(r"(?=(?:购|销)\s)")


def _clean_text_line(line: str) -> str:
    """去掉纵向拆分标签残留（购/买/方/信/息 等）后的行首噪声。"""
    return _NOISE_PREFIX_RE.sub("", line)


def _trim_contact_value(value: str) -> str:
    """截断地址值中混入的后续标签（公司电话/公司开户等）。"""
    return re.split(r"\s*公司(?:电话|开户|地址|名称)", value)[0].strip()


def _extract_parties_from_text(text: str) -> tuple[dict, dict]:
    """无表格时从纯文本提取买卖方信息。

    支持：分段标记（购买方/销售方）、行内交错（购 名称：A 销 名称：B）、
    纵向拆分标签（购/买/方/信/息 各占一行）、无标记顺序推断。
    """
    buyer = _empty_party()
    seller = _empty_party()
    current = "buyer"
    saw_marker = False

    def assign(segment: str, forced_side: str | None = None) -> None:
        nonlocal current
        for key, pattern in _LABEL_VALUE_RES:
            m = pattern.search(segment)
            if not m or not m.group(1).strip():
                continue
            side = forced_side or current
            if forced_side is None and not saw_marker and side == "buyer" and buyer.get(key) is not None:
                # 无买卖方标记时，同一字段第二次出现视为销售方
                side = "seller"
                current = "seller"
            if (
                forced_side is None
                and not saw_marker
                and "公司" in segment
                and key in ("address_phone", "bank_account")
            ):
                # “公司地址/公司开户银行账号”等备注式信息描述销售方
                side = "seller"
            target = seller if side == "seller" else buyer
            value = m.group(1).strip()
            if key == "tax_number":
                tm = _TAX_RUN_RE.search(value)
                value = tm.group(1) if tm else value
            elif key == "address_phone":
                value = _trim_contact_value(value)
            if target[key] is None and value:
                target[key] = value
            break

    for raw_line in text.split("\n"):
        line = normalize_fullwidth(raw_line.strip())
        if not line:
            continue
        side = _party_side(line)
        if side:
            current = side
            saw_marker = True
            continue

        parts = _INTERLEAVE_SPLIT_RE.split(line)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                pm = re.match(r"^(购|销)\s+", part)
                forced = ("buyer" if pm.group(1) == "购" else "seller") if pm else None
                segment = _clean_text_line(part[pm.end():] if pm else part)
                assign(segment, forced)
            continue

        clean = _clean_text_line(line)
        # 税号行可能同时含买卖双方两个税号，按出现顺序填充
        if ("纳税人识别号" in clean or "统一社会信用代码" in clean) and _TAX_RUN_RE.search(clean):
            runs = _TAX_RUN_RE.findall(clean)
            if len(runs) >= 2:
                if buyer["tax_number"] is None:
                    buyer["tax_number"] = runs[0]
                if seller["tax_number"] is None:
                    seller["tax_number"] = runs[1]
            elif runs:
                if current == "seller" and seller["tax_number"] is None:
                    seller["tax_number"] = runs[0]
                elif buyer["tax_number"] is None:
                    buyer["tax_number"] = runs[0]
                elif seller["tax_number"] is None:
                    seller["tax_number"] = runs[0]
            continue
        assign(clean)

    return buyer, seller


def _extract_seller_contact_from_text(text: str) -> tuple[str | None, str | None]:
    """从备注式文本行提取销售方联系方式（携程等模板将地址/开户行打印在备注区）。"""
    address_phone: str | None = None
    bank_account: str | None = None
    for raw_line in text.split("\n"):
        line = normalize_fullwidth(raw_line.strip())
        if not line:
            continue
        m = re.search(r"(?:公司地址|地址)\s*[：:]\s*(.+)", line)
        if m and address_phone is None:
            address_phone = _trim_contact_value(m.group(1))
        m = re.search(r"(?:公司开户银行账号|开户银行账号|开户行及账号|开户行|账号)\s*[：:]\s*(.+)", line)
        if m and bank_account is None:
            value = m.group(1).strip()
            num = re.search(r"([0-9][0-9\s\-]{4,})", value)
            bank_account = num.group(1).replace(" ", "") if num else value
    return address_phone, bank_account


# ---- 行项目明细 ---- #

def _find_item_columns(table_rows: list[list[str | None]]) -> tuple[dict[str, int] | None, int]:
    """在表格中定位列头行，返回 (字段->列索引 映射, 列头行号)。"""
    for row_idx, row in enumerate(table_rows):
        headers = [str(c or "").replace("\n", "") for c in row]
        col_map: dict[str, int] = {}
        for field, names in rules.TABLE_COLUMN_MAP.items():
            idx = rules.find_column_index(headers, names)
            if idx >= 0:
                col_map[field] = idx
        if len(col_map) >= 4:
            return col_map, row_idx
    return None, -1


def _row_cells(row: list[str | None], col_map: dict[str, int]) -> dict[str, str | None]:
    cells: dict[str, str | None] = {}
    for field, idx in col_map.items():
        value = row[idx] if idx < len(row) else None
        cells[field] = str(value).strip() if value else None
    return cells


def _is_total_row(text: str) -> bool:
    return bool(re.search(r"合\s*计|价税合计|小写", text))


def _extract_items_by_columns(
    table_rows: list[list[str | None]],
    header_row_idx: int,
    col_map: dict[str, int],
) -> list[dict]:
    items: list[dict] = []
    for row in table_rows[header_row_idx + 1:]:
        cells = _row_cells(row, col_map)
        name = cells.get("item_name")
        if not name or _is_total_row(name):
            continue
        amount = parse_amount(cells.get("amount"))
        tax_amount = parse_amount(cells.get("tax_amount"))
        unit_price = parse_amount(cells.get("unit_price"))
        if amount is None and tax_amount is None and unit_price is None:
            continue
        items.append({
            "line_no": len(items) + 1,
            "item_name": name,
            "specification": cells.get("specification"),
            "unit": cells.get("unit"),
            "quantity": parse_amount(cells.get("quantity")),
            "unit_price": unit_price,
            "amount": amount,
            "tax_rate": parse_tax_rate(cells.get("tax_rate") or ""),
            "tax_amount": tax_amount,
            "raw_row": " | ".join(str(c) for c in row if c),
        })
    return items


# 合并单元格兜底：行项目全部挤在一个单元格内时的正则启发式（模板适配，勿删）
_ITEM_PATTERN_WITH_QTY = re.compile(
    r"\*([^*]+)\*\s*(\S+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+(\d+\.?\d*)%\s+([\d.]+)"
)
_ITEM_PATTERN_NO_QTY = re.compile(
    r"\*([^*]+)\*\s*(\S+)\s+([\d.]+)\s+([\d.]+)\s+(\d+\.?\d*)%\s+([\d.]+)"
)


def _split_merged_qty_price(raw_unit_price: Decimal | None, raw_amount: Decimal | None) -> tuple[Decimal | None, Decimal | None]:
    """单价×数量被合并打印（如 5×17326.73 → 517326.73）时的启发式拆分。"""
    if (
        raw_unit_price is None
        or raw_amount is None
        or raw_amount <= 0
        or raw_unit_price <= raw_amount * 3
        or raw_unit_price <= 1000
    ):
        return None, raw_unit_price
    integer_part = int(raw_unit_price)
    fraction_part = raw_unit_price - integer_part
    if integer_part < 100:
        return None, raw_unit_price
    possible_qty = integer_part // 1000
    remaining = integer_part % 1000
    possible_up = Decimal(str(remaining)) + fraction_part
    if possible_qty >= 1 and abs(float(possible_up) - float(raw_amount)) < 1:
        return Decimal(str(possible_qty)), possible_up
    return None, raw_unit_price


def _build_item(
    line_no: int,
    name_group: str,
    spec_group: str,
    quantity: Decimal | None,
    unit_price: Decimal | None,
    amount: Decimal | None,
    tax_rate: Decimal | None,
    tax_amount: Decimal | None,
) -> dict:
    return {
        "line_no": line_no,
        "item_name": f"*{name_group}*{spec_group.strip()}",
        "specification": None,
        "unit": None,
        "quantity": quantity,
        "unit_price": unit_price,
        "amount": amount,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
    }


def _extract_items_from_merged_cells(table_rows: list[list[str | None]]) -> list[dict]:
    items: list[dict] = []

    for row in table_rows:
        if len(row) < 1:
            continue
        cell_text = str(row[0]) if row[0] else ""

        if not any(name in cell_text for name in ["项目名称", "合 计", "行项目"]):
            continue

        combined = cell_text.replace("\n", " ").replace("  ", " ")

        m = _ITEM_PATTERN_WITH_QTY.search(combined)
        if m:
            items.append(_build_item(
                1, m.group(1), m.group(2),
                parse_amount(m.group(4)), parse_amount(m.group(3)),
                parse_amount(m.group(5)), parse_tax_rate(m.group(6)),
                parse_amount(m.group(7)),
            ))
            continue

        m = _ITEM_PATTERN_NO_QTY.search(combined)
        if m:
            raw_unit_price = parse_amount(m.group(3))
            raw_amount = parse_amount(m.group(4))
            quantity, unit_price = _split_merged_qty_price(raw_unit_price, raw_amount)
            items.append(_build_item(
                1, m.group(1), m.group(2),
                quantity, unit_price, raw_amount,
                parse_tax_rate(m.group(5)), parse_amount(m.group(6)),
            ))
            continue

        for line in cell_text.split("\n"):
            line_norm = normalize_text(line)
            if not ("*" in line_norm and "%" in line_norm):
                continue

            m = _ITEM_PATTERN_WITH_QTY.search(line_norm)
            has_qty = True
            if not m:
                m = _ITEM_PATTERN_NO_QTY.search(line_norm)
                has_qty = False

            if m:
                if has_qty:
                    items.append(_build_item(
                        len(items) + 1, m.group(1), m.group(2),
                        parse_amount(m.group(4)), parse_amount(m.group(3)),
                        parse_amount(m.group(5)), parse_tax_rate(m.group(6)),
                        parse_amount(m.group(7)),
                    ))
                else:
                    raw_up = parse_amount(m.group(3))
                    raw_am = parse_amount(m.group(4))
                    qty, up = _split_merged_qty_price(raw_up, raw_am)
                    items.append(_build_item(
                        len(items) + 1, m.group(1), m.group(2),
                        qty, up, raw_am,
                        parse_tax_rate(m.group(5)), parse_amount(m.group(6)),
                    ))

        if items:
            break

    return items


def _extract_items_from_table_rows(table_rows: list[list[str | None]]) -> list[dict]:
    col_map, header_idx = _find_item_columns(table_rows)
    if col_map:
        items = _extract_items_by_columns(table_rows, header_idx, col_map)
        if items:
            return items
    return _extract_items_from_merged_cells(table_rows)


# ---- 金额 ---- #

def _find_total_row_index(table_rows: list[list[str | None]]) -> int:
    for i, row in enumerate(table_rows):
        for cell in row:
            if cell and _is_total_row(str(cell)):
                return i
    return -1


def _amounts_in_cell(cell: str) -> list[Decimal]:
    return [
        parsed
        for a in _AMOUNT_TOKEN_RE.findall(normalize_fullwidth(cell))
        if (parsed := parse_amount(a)) is not None
    ]


def _cell_value(row: list[str | None], idx: int | None) -> str | None:
    if idx is None or idx < 0 or idx >= len(row):
        return None
    value = row[idx]
    return str(value).strip() if value else None


def _extract_amounts_from_table(
    table_rows: list[list[str | None]],
    col_map: dict[str, int] | None = None,
    header_row_idx: int = -1,
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    """提取（不含税金额, 税额, 价税合计）。列定位优先，整行金额兜底。"""
    amount_excluding_tax: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None

    total_idx = _find_total_row_index(table_rows)
    if total_idx >= 0 and total_idx >= header_row_idx:
        row = table_rows[total_idx]

        # 列定位仅在金额列与税额列是不同单元格且各含单一金额时可信
        if col_map:
            amount_idx = col_map.get("amount")
            tax_idx = col_map.get("tax_amount")
            if amount_idx is not None and tax_idx is not None and amount_idx != tax_idx:
                amount_cell = _cell_value(row, amount_idx)
                tax_cell = _cell_value(row, tax_idx)
                amt_vals = _amounts_in_cell(amount_cell) if amount_cell else []
                tax_vals = _amounts_in_cell(tax_cell) if tax_cell else []
                if len(amt_vals) == 1 and len(tax_vals) == 1:
                    amount_excluding_tax, tax_amount = amt_vals[0], tax_vals[0]

        # 兜底：收集整行所有 ¥ 金额（不含“小写”单元格，那是价税合计）
        row_amounts: list[Decimal] = []
        for cell in row:
            if not cell:
                continue
            cell_text = normalize_fullwidth(str(cell))
            amounts = _amounts_in_cell(cell_text)
            if "小写" in cell_text:
                if amounts and total_amount is None:
                    total_amount = amounts[-1]
            elif amounts:
                row_amounts.extend(amounts)

        if amount_excluding_tax is None and row_amounts:
            amount_excluding_tax = row_amounts[0]
        if tax_amount is None and len(row_amounts) >= 2:
            tax_amount = row_amounts[1]
        if total_amount is None and len(row_amounts) >= 3:
            total_amount = row_amounts[2]

    if total_amount is None:
        for row in table_rows:
            for cell in row:
                if not cell:
                    continue
                cell_text = normalize_fullwidth(str(cell))
                if "小写" not in cell_text:
                    continue
                amounts = _amounts_in_cell(cell_text)
                if amounts:
                    total_amount = amounts[-1]
                    break
            if total_amount is not None:
                break

    return amount_excluding_tax, tax_amount, total_amount


def _extract_amounts_from_text(text: str) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    """无表格时从文本行提取金额（合计行 + 价税合计行）。"""
    amount_excluding_tax: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None

    for line in text.split("\n"):
        line_norm = normalize_fullwidth(line)
        if re.search(r"合\s*计", line_norm):
            amounts = _amounts_in_cell(line_norm)
            if len(amounts) >= 3:
                amount_excluding_tax, tax_amount, total_amount = amounts[0], amounts[1], amounts[2]
        elif "小写" in line_norm or "价税合计" in line_norm:
            amounts = _amounts_in_cell(line_norm)
            if amounts and total_amount is None:
                total_amount = amounts[0]

    return amount_excluding_tax, tax_amount, total_amount


# ---- 置信度 ---- #

def _compute_confidence(invoice_data: dict, items: list[dict]) -> float:
    field_count = 0
    for field in _CONFIDENCE_FIELDS:
        val = invoice_data.get(field)
        if val is not None and val != "" and val != Decimal("0"):
            field_count += 1
    if items:
        field_count += min(len(items), 3)
    return min(round(field_count / rules.EXPECTED_HEADER_FIELDS, 2), 1.0)


# ---- 主入口 ---- #

def parse_invoice(extraction: ExtractionResult) -> dict:
    invoice_data: dict = {}
    warnings: list[str] = []
    text = extraction.raw_text

    invoice_data["invoice_name"] = _extract_invoice_name(extraction.raw_text, extraction.pages)
    invoice_data["invoice_code"] = _extract_invoice_code(text)
    invoice_data["invoice_number"] = _extract_invoice_number(text)

    date_raw = _extract_value_after_keyword(text, "issue_date")
    invoice_data["issue_date"] = parse_date(date_raw) if date_raw else None
    invoice_data["check_code"] = _extract_check_code(text)
    invoice_data["machine_number"] = _extract_machine_number(text)

    all_tables: list[list[list[str | None]]] = []
    for page in extraction.pages:
        for table in page.tables:
            if table:
                all_tables.append(table)

    buyer_info = _empty_party()
    seller_info = _empty_party()
    items: list[dict] = []
    amount_excluding_tax: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None

    if all_tables:
        primary_table = all_tables[0]

        buyer_info, seller_info = _parse_party_from_table(primary_table)
        items = _extract_items_from_table_rows(primary_table)

        col_map, header_idx = _find_item_columns(primary_table)
        amount_excluding_tax, tax_amount, total_amount = _extract_amounts_from_table(
            primary_table, col_map, header_idx,
        )

    if not buyer_info["name"] and not seller_info["name"]:
        text_buyer, text_seller = _extract_parties_from_text(text)
        _merge_party(buyer_info, text_buyer)
        _merge_party(seller_info, text_seller)

    if not buyer_info["name"]:
        buyer_info["name"] = _extract_value_after_keyword(text, "buyer_name")
    if not seller_info["name"]:
        seller_info["name"] = _extract_value_after_keyword(text, "seller_name")

    # 备注区的“公司地址/公司开户银行账号”（携程等模板）归属销售方
    if seller_info["address_phone"] is None or seller_info["bank_account"] is None:
        contact_address, contact_bank = _extract_seller_contact_from_text(text)
        if seller_info["address_phone"] is None and contact_address:
            seller_info["address_phone"] = contact_address
        if seller_info["bank_account"] is None and contact_bank:
            seller_info["bank_account"] = contact_bank

    if amount_excluding_tax is None and tax_amount is None and total_amount is None:
        amount_excluding_tax, tax_amount, total_amount = _extract_amounts_from_text(text)

    invoice_data["buyer_name"] = buyer_info["name"]
    invoice_data["buyer_tax_number"] = buyer_info["tax_number"]
    invoice_data["buyer_address_phone"] = buyer_info["address_phone"]
    invoice_data["buyer_bank_account"] = buyer_info["bank_account"]
    invoice_data["seller_name"] = seller_info["name"]
    invoice_data["seller_tax_number"] = seller_info["tax_number"]
    invoice_data["seller_address_phone"] = seller_info["address_phone"]
    invoice_data["seller_bank_account"] = seller_info["bank_account"]

    invoice_data["amount_excluding_tax"] = amount_excluding_tax
    invoice_data["tax_amount"] = tax_amount
    invoice_data["total_amount"] = total_amount

    if total_amount and tax_amount and not amount_excluding_tax:
        amount_excluding_tax = total_amount - tax_amount
        invoice_data["amount_excluding_tax"] = amount_excluding_tax
    elif total_amount and amount_excluding_tax and not tax_amount:
        tax_amount = total_amount - amount_excluding_tax
        invoice_data["tax_amount"] = tax_amount
    elif amount_excluding_tax and tax_amount and not total_amount:
        total_amount = amount_excluding_tax + tax_amount
        invoice_data["total_amount"] = total_amount

    invoice_data["total_amount_text"] = _extract_chinese_amount(text)
    invoice_data["remarks"] = _extract_value_after_keyword(text, "remarks")

    type_raw = _extract_value_after_keyword(text, "invoice_type")
    if not type_raw and invoice_data["invoice_name"]:
        type_raw = invoice_data["invoice_name"]
    invoice_data["invoice_type"] = type_raw

    if not items:
        warnings.append("未提取到行项目明细")

    # 数电票（全电发票）无发票代码，仅当文本中出现该关键词却未提取到时告警
    if invoice_data.get("invoice_code") is None and "发票代码" in text:
        warnings.append("未提取到字段: invoice_code")

    for field_name in [
        "invoice_number", "issue_date",
        "buyer_name", "seller_name", "total_amount",
    ]:
        if invoice_data.get(field_name) is None:
            warnings.append(f"未提取到字段: {field_name}")

    invoice_data["currency"] = "CNY"
    invoice_data["parser_warnings"] = warnings
    invoice_data["parse_confidence"] = _compute_confidence(invoice_data, items)
    invoice_data["items"] = items
    invoice_data["raw_text"] = text
    invoice_data["page_count"] = extraction.page_count

    return invoice_data
