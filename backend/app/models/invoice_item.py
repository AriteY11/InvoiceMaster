from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    line_no: Mapped[int] = mapped_column(default=1)
    item_name: Mapped[str | None] = mapped_column(String(255), index=True)
    specification: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 10))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    raw_row: Mapped[str | None] = mapped_column(Text)

    invoice: Mapped["Invoice"] = relationship(back_populates="items")
