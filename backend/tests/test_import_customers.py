import pytest

from app.api.schemas.customer import CustomerType
from scripts.import_customers import parse_row

ROW = {
    "客戶名稱": "測試店",
    "發票抬頭": "",
    "統編": "12345678",
    "聯絡電話": "",
    "縣市": "苗栗縣",
    "地址": "",
    "主要聯絡人": "",
    "客戶類型": "房仲",
}


def test_parse_row_fills_placeholders_and_maps_type():
    c = parse_row(ROW)
    assert c.contact_phone == "99999999"
    assert c.address == "台灣"
    assert c.primary_contact == "負責人"
    assert c.invoice_number == "12345678"
    assert c.invoice_title is None
    assert c.customer_type == CustomerType.REAL_ESTATE


def test_parse_row_rejects_missing_city():
    with pytest.raises(ValueError):
        parse_row({**ROW, "縣市": ""})
