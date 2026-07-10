from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db import get_db
from ...schemas.stats import StatsCategoryResponse, StatsOverviewResponse, StatsTrendResponse
from ...services.stats_service import get_categories, get_overview, get_trends

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewResponse)
def stats_overview(db: Session = Depends(get_db)) -> StatsOverviewResponse:
    return get_overview(db)


@router.get("/trends", response_model=StatsTrendResponse)
def stats_trends(
    group_by: str = Query("month", pattern="^(month|day)$"),
    db: Session = Depends(get_db),
) -> StatsTrendResponse:
    return get_trends(db, group_by=group_by)


@router.get("/categories", response_model=StatsCategoryResponse)
def stats_categories(
    dimension: str = Query("invoice_type", pattern="^(invoice_type|seller_name|item_name)$"),
    db: Session = Depends(get_db),
) -> StatsCategoryResponse:
    return get_categories(db, dimension=dimension)
