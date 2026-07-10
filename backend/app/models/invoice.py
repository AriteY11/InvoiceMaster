from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Float, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    page_count: Mapped[int] = mapped_column(default=0)

    invoice_name: Mapped[str | None] = mapped_column(String(255))
    invoice_code: Mapped[str | None] = mapped_column(String(32), index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(32), index=True)
    issue_date: Mapped[date | None] = mapped_column(Date, index=True)
    check_code: Mapped[str | None] = mapped_column(String(64))
    machine_number: Mapped[str | None] = mapped_column(String(64))
    invoice_type: Mapped[str | None] = mapped_column(String(100), index=True)
    currency: Mapped[str] = mapped_column(String(16), default="CNY")

    buyer_name: Mapped[str | None] = mapped_column(String(255), index=True)
    buyer_tax_number: Mapped[str | None] = mapped_column(String(64))
    buyer_address_phone: Mapped[str | None] = mapped_column(String(255))
    buyer_bank_account: Mapped[str | None] = mapped_column(String(255))

    seller_name: Mapped[str | None] = mapped_column(String(255), index=True)
    seller_tax_number: Mapped[str | None] = mapped_column(String(64))
    seller_address_phone: Mapped[str | None] = mapped_column(String(255))
    seller_bank_account: Mapped[str | None] = mapped_column(String(255))

    amount_excluding_tax: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), index=True)
    total_amount_text: Mapped[str | None] = mapped_column(String(255))

    remarks: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parser_warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    parse_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    parse_status: Mapped[str] = mapped_column(String(32), default="parsed", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.line_no",
    )
