from __future__ import annotations

import re

from sqlalchemy import func

from ..models.invoice import Invoice
from ..models.invoice_item import InvoiceItem
from ..schemas.stats import CategoryPoint, StatsCategoryResponse, StatsOverviewResponse, StatsTrendResponse, TrendPoint


def extract_service_category(item_name: str | None) -> str:
    if not item_name:
        return "未分类"
    m = re.search(r"\*([^*]+)\*", item_name)
    if m:
        return m.group(1)
    return item_name[:20] if len(item_name) > 20 else item_name


def get_overview(db) -> StatsOverviewResponse:
    result = (
        db.query(
            func.count(Invoice.id).label("total"),
            func.coalesce(func.sum(Invoice.total_amount), 0).label("total_amount"),
            func.coalesce(func.sum(Invoice.tax_amount), 0).label("total_tax"),
            func.max(Invoice.issue_date).label("latest_date"),
        )
        .filter(Invoice.parse_status == "parsed")
        .first()
    )
    return StatsOverviewResponse(
        total_invoices=result.total or 0,
        total_amount=result.total_amount or 0,
        total_tax_amount=result.total_tax or 0,
        latest_issue_date=result.latest_date,
    )


def get_trends(db, group_by: str = "month") -> StatsTrendResponse:
    if group_by == "day":
        period_expr = func.strftime("%Y-%m-%d", Invoice.issue_date)
    else:
        period_expr = func.strftime("%Y-%m", Invoice.issue_date)

    rows = (
        db.query(
            period_expr.label("period"),
            func.count(Invoice.id).label("cnt"),
            func.coalesce(func.sum(Invoice.total_amount), 0).label("amt"),
            func.coalesce(func.sum(Invoice.tax_amount), 0).label("tax"),
        )
        .filter(Invoice.parse_status == "parsed", Invoice.issue_date.isnot(None))
        .group_by("period")
        .order_by("period")
        .all()
    )

    items = [
        TrendPoint(
            period=row.period,
            invoice_count=row.cnt,
            total_amount=row.amt or 0,
            tax_amount=row.tax or 0,
        )
        for row in rows
    ]
    return StatsTrendResponse(group_by=group_by, items=items)


def get_categories(db, dimension: str = "invoice_type") -> StatsCategoryResponse:
    if dimension == "seller_name":
        col = Invoice.seller_name
        rows = (
            db.query(
                func.coalesce(col, "未分类").label("name"),
                func.count(Invoice.id).label("cnt"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("amt"),
            )
            .filter(Invoice.parse_status == "parsed")
            .group_by("name")
            .order_by(func.count(Invoice.id).desc())
            .limit(20)
            .all()
        )
    elif dimension == "item_name":
        rows = (
            db.query(
                InvoiceItem.item_name.label("name"),
                func.count(func.distinct(InvoiceItem.invoice_id)).label("cnt"),
                func.coalesce(func.sum(InvoiceItem.amount), 0).label("amt"),
            )
            .filter(InvoiceItem.item_name.isnot(None))
            .group_by("name")
            .order_by(func.sum(InvoiceItem.amount).desc())
            .limit(20)
            .all()
        )
        rows = [r._asdict() for r in rows]
        merged = {}
        for r in rows:
            category = extract_service_category(r["name"])
            if category not in merged:
                merged[category] = {"cnt": 0, "amt": 0}
            merged[category]["cnt"] += r["cnt"]
            merged[category]["amt"] += r["amt"]
        rows_type = type("Row", (), {})
        rows = [
            rows_type()
            for _ in merged
        ]
        for i, (k, v) in enumerate(sorted(merged.items(), key=lambda x: x[1]["amt"], reverse=True)):
            rows[i].name = k
            rows[i].cnt = v["cnt"]
            rows[i].amt = v["amt"]
    else:
        col = Invoice.invoice_type
        rows = (
            db.query(
                func.coalesce(col, "未分类").label("name"),
                func.count(Invoice.id).label("cnt"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("amt"),
            )
            .filter(Invoice.parse_status == "parsed")
            .group_by("name")
            .order_by(func.count(Invoice.id).desc())
            .limit(20)
            .all()
        )

    items = [
        CategoryPoint(
            name=row.name,
            count=row.cnt,
            total_amount=row.amt or 0,
        )
        for row in rows
    ]
    return StatsCategoryResponse(dimension=dimension, items=items)
