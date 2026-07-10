from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_no: int
    item_name: str | None = None
    specification: str | None = None
    unit: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    amount: Decimal | None = None
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    raw_row: str | None = None


class InvoiceSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    invoice_name: str | None = None
    invoice_code: str | None = None
    invoice_number: str | None = None
    issue_date: date | None = None
    invoice_type: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None
    total_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    parse_status: str
    parse_confidence: float
    created_at: datetime


class InvoiceDetailRead(InvoiceSummaryRead):
    page_count: int = 0
    check_code: str | None = None
    machine_number: str | None = None
    currency: str | None = None
    buyer_tax_number: str | None = None
    buyer_address_phone: str | None = None
    buyer_bank_account: str | None = None
    seller_tax_number: str | None = None
    seller_address_phone: str | None = None
    seller_bank_account: str | None = None
    amount_excluding_tax: Decimal | None = None
    total_amount_text: str | None = None
    remarks: str | None = None
    raw_text: str | None = None
    parser_warnings: list[str] = Field(default_factory=list)
    items: list[InvoiceItemRead] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    items: list[InvoiceSummaryRead]
    total: int
    page: int
    page_size: int


class UploadInvoiceResult(BaseModel):
    file_name: str
    invoice_id: int | None = None
    status: str
    message: str
    duplicate: bool = False


class UploadInvoicesResponse(BaseModel):
    results: list[UploadInvoiceResult]


class DeleteInvoiceResponse(BaseModel):
    message: str
