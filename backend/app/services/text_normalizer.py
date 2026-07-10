from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

FULLWIDTH_DIGIT_MAP = str.maketrans("０１２３４５６７８９", "0123456789")
FULLWIDTH_LETTER_UPPER = str.maketrans(
    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
)
FULLWIDTH_LETTER_LOWER = str.maketrans(
    "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
    "abcdefghijklmnopqrstuvwxyz",
)

CNY_SYMBOLS = re.compile(r"[￥¥]")
AMOUNT_CLEANUP = re.compile(r"[^\d.\-]")
MULTI_SPACE = re.compile(r"[ \t\u3000]+")
MULTI_NEWLINE = re.compile(r"\n{3,}")


def normalize_fullwidth(text: str) -> str:
    result = text.translate(FULLWIDTH_DIGIT_MAP)
    result = result.translate(FULLWIDTH_LETTER_UPPER)
    result = result.translate(FULLWIDTH_LETTER_LOWER)
    return result


def normalize_whitespace(text: str) -> str:
    result = MULTI_SPACE.sub(" ", text)
    result = MULTI_NEWLINE.sub("\n\n", result)
    return result.strip()


def normalize_text(text: str) -> str:
    return normalize_whitespace(normalize_fullwidth(text))


def parse_amount(raw: str) -> Decimal | None:
    if not raw:
        return None
    cleaned = CNY_SYMBOLS.sub("", raw)
    cleaned = cleaned.replace(",", "").replace("，", "")
    cleaned = cleaned.replace(" ", "").replace("\u3000", "")
    cleaned = AMOUNT_CLEANUP.sub("", cleaned)
    if not cleaned or cleaned == "-":
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_tax_rate(raw: str) -> Decimal | None:
    if not raw:
        return None
    cleaned = raw.replace(" ", "").replace("%", "").replace("％", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_date(raw: str) -> date | None:
    if not raw:
        return None

    patterns: list[tuple[str, str]] = [
        (r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", "ymd"),
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "ymd"),
        (r"(\d{4})/(\d{1,2})/(\d{1,2})", "ymd"),
        (r"(\d{4})\.(\d{1,2})\.(\d{1,2})", "ymd"),
        (r"(\d{1,2})/(\d{1,2})/(\d{4})", "mdy"),
    ]

    for pattern, fmt in patterns:
        m = re.search(pattern, raw)
        if m:
            try:
                if fmt == "ymd":
                    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                else:
                    return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
            except ValueError:
                continue
    return None
