from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StatsOverviewResponse(BaseModel):
    total_invoices: int
    total_amount: Decimal
    total_tax_amount: Decimal
    latest_issue_date: date | None = None


class TrendPoint(BaseModel):
    period: str
    invoice_count: int
    total_amount: Decimal
    tax_amount: Decimal


class StatsTrendResponse(BaseModel):
    group_by: str
    items: list[TrendPoint]


class CategoryPoint(BaseModel):
    name: str
    count: int
    total_amount: Decimal


class StatsCategoryResponse(BaseModel):
    dimension: str
    items: list[CategoryPoint]
