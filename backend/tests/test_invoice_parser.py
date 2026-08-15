from datetime import date
from decimal import Decimal

from app.services.invoice_parser import (
    _compute_confidence,
    _extract_amounts_from_table,
    _extract_amounts_from_text,
    _extract_check_code,
    _extract_invoice_code,
    _extract_invoice_number,
    _extract_items_from_merged_cells,
    _extract_items_from_table_rows,
    _extract_machine_number,
    _extract_parties_from_text,
    _extract_seller_contact_from_text,
    _is_party_cell,
    _parse_party_block,
    _split_merged_qty_price,
)

SAMPLE_TEXT = """电子发票（普通发票）
发票号码：24312000000012345678
发票代码：123456789012
开票日期：2024年01月15日
校验码：12345 67890 12345 67890
机器编号：6610123456789012
购买方信息
名称：上海测试科技有限公司
统一社会信用代码/纳税人识别号：91310115MA1K3X6Y5Z
地址、电话：上海市浦东新区xx路1号 021-12345678
开户行及账号：中国银行上海分行 123456789012
销售方信息
名称：北京云服务有限公司
统一社会信用代码/纳税人识别号：91110108MA01ABCDEF
地址、电话：北京市海淀区xx路2号 010-87654321
开户行及账号：工商银行北京分行 987654321098
价税合计（大写）壹仟零陆拾元整 （小写）¥1060.00
备注：测试备注
"""


def test_extract_invoice_code():
    assert _extract_invoice_code(SAMPLE_TEXT) == "123456789012"


def test_extract_invoice_number():
    assert _extract_invoice_number(SAMPLE_TEXT) == "24312000000012345678"


def test_extract_check_code():
    assert _extract_check_code(SAMPLE_TEXT) == "12345678901234567890"


def test_extract_machine_number():
    assert _extract_machine_number(SAMPLE_TEXT) == "6610123456789012"


def test_parse_party_block():
    block = _parse_party_block([
        "名称：上海测试科技有限公司",
        "统一社会信用代码/纳税人识别号：91310115MA1K3X6Y5Z",
        "地址、电话：上海市浦东新区xx路1号 021-12345678",
        "开户行及账号：中国银行上海分行 123456789012",
    ])
    assert block["name"] == "上海测试科技有限公司"
    assert block["tax_number"] == "91310115MA1K3X6Y5Z"
    assert block["address_phone"].startswith("上海市浦东新区")
    assert block["bank_account"].startswith("中国银行")


def test_parse_party_block_multiline_value():
    block = _parse_party_block([
        "名称：上海测试科技有限公司",
        "统一社会信用代码/纳税人识别号：",
        "91310115MA1K3X6Y5Z",
        "地址、电话：上海市浦东新区xx路1号",
    ])
    assert block["tax_number"] == "91310115MA1K3X6Y5Z"
    assert block["address_phone"].startswith("上海市浦东新区")


def test_extract_parties_from_text():
    buyer, seller = _extract_parties_from_text(SAMPLE_TEXT)
    assert buyer["name"] == "上海测试科技有限公司"
    assert buyer["tax_number"] == "91310115MA1K3X6Y5Z"
    assert buyer["address_phone"].startswith("上海市浦东新区")
    assert buyer["bank_account"].startswith("中国银行")
    assert seller["name"] == "北京云服务有限公司"
    assert seller["tax_number"] == "91110108MA01ABCDEF"
    assert seller["bank_account"].startswith("工商银行")


def test_extract_parties_from_text_without_markers():
    text = (
        "名称：上海测试科技有限公司\n"
        "统一社会信用代码/纳税人识别号：91310115MA1K3X6Y5Z\n"
        "地址、电话：上海市浦东新区xx路1号\n"
        "开户行及账号：中国银行上海分行 123456789012\n"
        "名称：北京云服务有限公司\n"
        "统一社会信用代码/纳税人识别号：91110108MA01ABCDEF\n"
        "地址、电话：北京市海淀区xx路2号\n"
        "开户行及账号：工商银行北京分行 987654321098\n"
    )
    buyer, seller = _extract_parties_from_text(text)
    assert buyer["name"] == "上海测试科技有限公司"
    assert buyer["tax_number"] == "91310115MA1K3X6Y5Z"
    assert buyer["address_phone"].startswith("上海市浦东新区")
    assert seller["name"] == "北京云服务有限公司"
    assert seller["tax_number"] == "91110108MA01ABCDEF"


def test_extract_parties_from_text_interleaved():
    text = (
        "购 名称：上海测试科技有限公司 销 名称：北京云服务有限公司\n"
        "买 售\n"
        "方 方\n"
        "信 统一社会信用代码/纳税人识别号：91310115MA1K3X6Y5Z "
        "信 统一社会信用代码/纳税人识别号：91110108MA01ABCDEF\n"
        "息 息\n"
    )
    buyer, seller = _extract_parties_from_text(text)
    assert buyer["name"] == "上海测试科技有限公司"
    assert buyer["tax_number"] == "91310115MA1K3X6Y5Z"
    assert seller["name"] == "北京云服务有限公司"
    assert seller["tax_number"] == "91110108MA01ABCDEF"


def test_is_party_cell_excludes_bank_name():
    assert not _is_party_cell(
        "公司地址：上海市松江区xx路1号 公司电话：13585785994 "
        "公司开户银行名称：上海农村商业银行石湖荡支行"
    )
    assert _is_party_cell("名称：上海测试科技有限公司\n统一社会信用代码/纳税人识别号：91310115MA1K3X6Y5Z")


def test_extract_seller_contact_from_text():
    text = (
        "公司地址：上海市松江区石湖荡镇石湖新路95号 公司电话：13585785994 "
        "公司开户银行名称：上海农村商业银行股份有限公司石湖荡支行\n"
        "公司开户银行账号：50131000551708444\n"
    )
    address, bank = _extract_seller_contact_from_text(text)
    assert address == "上海市松江区石湖荡镇石湖新路95号"
    assert bank == "50131000551708444"


def test_extract_items_from_merged_cells():
    rows = [[
        "项目名称\n"
        "*信息技术服务*云服务费 1000.00 1 1000.00 6% 60.00\n"
        "合 计 ¥1000.00 ¥60.00 ¥1060.00",
    ]]
    items = _extract_items_from_merged_cells(rows)
    assert len(items) == 1
    item = items[0]
    assert item["item_name"] == "*信息技术服务*云服务费"
    assert item["quantity"] == Decimal("1")
    assert item["unit_price"] == Decimal("1000.00")
    assert item["amount"] == Decimal("1000.00")
    assert item["tax_rate"] == Decimal("6")
    assert item["tax_amount"] == Decimal("60.00")


def test_extract_items_by_columns():
    rows = [
        ["项目名称", "规格型号", "单位", "数量", "单价", "金额", "税率", "税额"],
        ["*信息技术服务*云服务费", "", "项", "1", "1000.00", "1000.00", "6%", "60.00"],
        ["合 计", "", "", "", "", "¥1000.00", "", "¥60.00"],
    ]
    items = _extract_items_from_table_rows(rows)
    assert len(items) == 1
    item = items[0]
    assert item["item_name"] == "*信息技术服务*云服务费"
    assert item["quantity"] == Decimal("1")
    assert item["amount"] == Decimal("1000.00")
    assert item["tax_rate"] == Decimal("6")
    assert item["tax_amount"] == Decimal("60.00")


def test_extract_amounts_from_table():
    rows = [
        ["项目名称", "金额", "税率", "税额"],
        ["*信息技术服务*云服务费", "1000.00", "6%", "60.00"],
        ["合 计 ¥1000.00 ¥60.00", "¥1000.00", "", "¥60.00", "¥1060.00(小写)"],
    ]
    amount_ex, tax_am, total = _extract_amounts_from_table(rows)
    assert amount_ex == Decimal("1000.00")
    assert tax_am == Decimal("60.00")
    assert total == Decimal("1060.00")


def test_extract_amounts_from_text():
    text = "合 计 ¥1000.00 ¥60.00 ¥1060.00\n价税合计（大写）壹仟零陆拾元整 （小写）¥1060.00"
    amount_ex, tax_am, total = _extract_amounts_from_text(text)
    assert amount_ex == Decimal("1000.00")
    assert tax_am == Decimal("60.00")
    assert total == Decimal("1060.00")


def test_split_merged_qty_price():
    qty, up = _split_merged_qty_price(Decimal("1123.45"), Decimal("123.45"))
    assert qty == Decimal("1")
    assert up == Decimal("123.45")


def test_split_merged_qty_price_no_split():
    qty, up = _split_merged_qty_price(Decimal("1000.00"), Decimal("1000.00"))
    assert qty is None
    assert up == Decimal("1000.00")


def test_compute_confidence():
    data = {
        "invoice_name": "电子发票（普通发票）",
        "invoice_code": "123456789012",
        "invoice_number": "24312000000012345678",
        "issue_date": date(2024, 1, 15),
        "check_code": "12345678901234567890",
        "machine_number": "6610123456789012",
        "invoice_type": "电子发票（普通发票）",
        "buyer_name": "上海测试科技有限公司",
        "buyer_tax_number": "91310115MA1K3X6Y5Z",
        "buyer_address_phone": "上海市",
        "buyer_bank_account": "中国银行",
        "seller_name": "北京云服务有限公司",
        "seller_tax_number": "91110108MA01ABCDEF",
        "seller_address_phone": "北京市",
        "seller_bank_account": "工商银行",
        "amount_excluding_tax": Decimal("1000.00"),
        "tax_amount": Decimal("60.00"),
        "total_amount": Decimal("1060.00"),
        "total_amount_text": "壹仟零陆拾元整",
        "remarks": "测试备注",
    }
    assert _compute_confidence(data, [{"x": 1}]) == 1.0
    empty = {k: None for k in data}
    assert _compute_confidence(empty, []) == 0.0
