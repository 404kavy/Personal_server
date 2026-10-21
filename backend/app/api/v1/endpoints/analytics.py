from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    DailyAnalyticsSummary,
    DistractionBreakdownItem,
    PeriodComparisonResponse,
    TimelineBlock,
)
from app.services.analytics_service import (
    compare_activity_periods,
    get_daily_summary,
    get_distraction_breakdown,
    get_timeline,
)

router = APIRouter(prefix="/analytics", tags=["Activity Analytics"])


def get_default_today() -> str:
    """Helper to return current UTC date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@router.get(
    "/summary/daily",
    response_model=DailyAnalyticsSummary,
    summary="Get daily activity summary and statistics",
)
async def get_daily_activity_summary(
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format (defaults to today)"),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated daily breakdown:
    - Total study duration, gaming duration, and distraction duration
    - Study to gaming ratio
    - Ranked list of top applications used
    """
    target_date = date or get_default_today()
    return get_daily_summary(db, target_date)


@router.get(
    "/distractions",
    response_model=List[DistractionBreakdownItem],
    summary="Get top distraction apps and websites",
)
async def get_distractions(
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format (defaults to today)"),
    limit: int = Query(5, ge=1, le=20, description="Max items to return"),
    db: Session = Depends(get_db),
):
    """
    Identifies non-productive time sinks for a specific date:
    - Ranked list of entertainment apps and websites with durations and percentages
    """
    target_date = date or get_default_today()
    return get_distraction_breakdown(db, target_date, limit=limit)


@router.get(
    "/compare",
    response_model=PeriodComparisonResponse,
    summary="Compare activity between two time periods",
)
async def compare_periods(
    start_a: str = Query(..., description="Start date for Period A (YYYY-MM-DD)"),
    end_a: str = Query(..., description="End date for Period A (YYYY-MM-DD)"),
    start_b: str = Query(..., description="Start date for Period B (YYYY-MM-DD)"),
    end_b: str = Query(..., description="End date for Period B (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Performs comparative trend analysis between two distinct time periods:
    - Calculates hours delta for study and gaming
    - Calculates percentage changes
    - Returns natural language summary
    """
    return compare_activity_periods(db, start_a, end_a, start_b, end_b)


@router.get(
    "/timeline",
    response_model=List[TimelineBlock],
    summary="Get chronological timeline of sessions for a day",
)
async def get_day_timeline(
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format (defaults to today)"),
    db: Session = Depends(get_db),
):
    """
    Returns chronological timeline session blocks for rendering day charts and visual timelines.
    """
    target_date = date or get_default_today()
    return get_timeline(db, target_date)
