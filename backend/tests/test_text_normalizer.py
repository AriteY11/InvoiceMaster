from datetime import date
from decimal import Decimal

from app.services.text_normalizer import (
    normalize_fullwidth,
    normalize_text,
    parse_amount,
    parse_date,
    parse_tax_rate,
)


def test_normalize_fullwidth():
    assert normalize_fullwidth("１２３ＡＢＣ") == "123ABC"
    assert normalize_fullwidth("１．５") == "1.5"


def test_normalize_text_whitespace():
    assert normalize_text("  a\u3000\u3000b  ") == "a b"


def test_parse_amount():
    assert parse_amount("¥1,234.56") == Decimal("1234.56")
    assert parse_amount("￥１２３．４５") == Decimal("123.45")
    assert parse_amount("1000.00") == Decimal("1000.00")
    assert parse_amount("") is None
    assert parse_amount("-") is None
    assert parse_amount("abc") is None


def test_parse_tax_rate():
    assert parse_tax_rate("6%") == Decimal("6")
    assert parse_tax_rate("6.5％") == Decimal("6.5")
    assert parse_tax_rate("不征税") is None


def test_parse_date():
    assert parse_date("2024年01月15日") == date(2024, 1, 15)
    assert parse_date("2024-1-5") == date(2024, 1, 5)
    assert parse_date("2024/01/15") == date(2024, 1, 15)
    assert parse_date("2024.01.15") == date(2024, 1, 15)
    assert parse_date("01/15/2024") == date(2024, 1, 15)
    assert parse_date("无日期") is None
    assert parse_date("2024年13月40日") is None
