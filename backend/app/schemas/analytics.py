from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CategoryBreakdown(BaseModel):
    category: str
    duration_seconds: int
    duration_formatted: str
    percentage: float


class AppUsageItem(BaseModel):
    identifier: str
    category: str
    duration_seconds: int
    duration_formatted: str
    percentage: float


class DailyAnalyticsSummary(BaseModel):
    date: str
    total_active_seconds: int
    total_study_seconds: int
    total_gaming_seconds: int
    total_entertainment_seconds: int
    total_unclassified_seconds: int
    study_hours: float
    gaming_hours: float
    entertainment_hours: float
    study_to_gaming_ratio: Optional[str] = None
    categories: List[CategoryBreakdown]
    top_apps: List[AppUsageItem]


class DistractionBreakdownItem(BaseModel):
    identifier: str
    duration_seconds: int
    duration_formatted: str
    percentage_of_distraction: float
    session_count: int


class PeriodMetrics(BaseModel):
    period_label: str
    start_date: str
    end_date: str
    total_study_seconds: int
    total_gaming_seconds: int
    study_hours: float
    gaming_hours: float


class PeriodComparisonResponse(BaseModel):
    period_a: PeriodMetrics
    period_b: PeriodMetrics
    study_delta_hours: float
    gaming_delta_hours: float
    study_change_percent: Optional[float] = None
    gaming_change_percent: Optional[float] = None
    summary: str


class TimelineBlock(BaseModel):
    id: int
    identifier: str
    category: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    duration_formatted: str

    class Config:
        from_attributes = True
