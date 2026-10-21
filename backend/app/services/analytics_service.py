from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Tuple, Union
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import ActivitySession, DailySummary
from app.schemas.activity import ActivityCategory


def format_seconds(seconds: int) -> str:
    """Formats raw seconds into human-readable duration strings (e.g., '2h 15m' or '45m')."""
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        sec = seconds % 60
        return f"{minutes}m {sec}s" if sec > 0 else f"{minutes}m"
    hours = minutes // 60
    rem_min = minutes % 60
    return f"{hours}h {rem_min}m" if rem_min > 0 else f"{hours}h"


def normalize_date(target_date: Union[date, str]) -> str:
    """Normalizes date input into YYYY-MM-DD string."""
    if isinstance(target_date, str):
        return target_date.strip()
    return target_date.strftime("%Y-%m-%d")


def get_daily_summary(db: Session, target_date: Union[date, str]) -> Dict[str, Any]:
    """
    Computes deterministic daily statistics from recorded sessions:
    - Calculates total active time, study time, gaming time, and distraction time.
    - Computes study-to-gaming ratio.
    - Lists top applications used.
    - Updates the DailySummary database table cache.
    """
    date_str = normalize_date(target_date)
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    sessions = (
        db.query(ActivitySession)
        .filter(func.date(ActivitySession.start_time) == date_str)
        .all()
    )

    category_totals: Dict[str, int] = {
        ActivityCategory.STUDY.value: 0,
        ActivityCategory.GAMING.value: 0,
        ActivityCategory.ENTERTAINMENT.value: 0,
        ActivityCategory.NEUTRAL.value: 0,
        ActivityCategory.UNCLASSIFIED.value: 0,
    }

    app_totals: Dict[str, Dict[str, Any]] = {}
    total_active_seconds = 0

    for s in sessions:
        dur = s.duration_seconds
        total_active_seconds += dur
        cat = s.category or ActivityCategory.NEUTRAL.value
        category_totals[cat] = category_totals.get(cat, 0) + dur

        ident = s.identifier
        if ident not in app_totals:
            app_totals[ident] = {"duration_seconds": 0, "category": cat}
        app_totals[ident]["duration_seconds"] += dur

    study_sec = category_totals[ActivityCategory.STUDY.value]
    gaming_sec = category_totals[ActivityCategory.GAMING.value]
    distract_sec = category_totals[ActivityCategory.ENTERTAINMENT.value]
    unclass_sec = category_totals[ActivityCategory.UNCLASSIFIED.value]

    # Calculate Study to Gaming Ratio
    if gaming_sec > 0:
        ratio_str = f"{round(study_sec / gaming_sec, 2)}:1"
    elif study_sec > 0:
        ratio_str = "100% study"
    else:
        ratio_str = "0:0"

    # Category breakdown list
    categories_list = []
    for cat_name, dur in category_totals.items():
        if dur > 0 or cat_name in [ActivityCategory.STUDY.value, ActivityCategory.GAMING.value, ActivityCategory.ENTERTAINMENT.value]:
            pct = round((dur / total_active_seconds * 100), 1) if total_active_seconds > 0 else 0.0
            categories_list.append(
                {
                    "category": cat_name,
                    "duration_seconds": dur,
                    "duration_formatted": format_seconds(dur),
                    "percentage": pct,
                }
            )

    # Top apps breakdown (ranked by usage)
    sorted_apps = sorted(app_totals.items(), key=lambda x: x[1]["duration_seconds"], reverse=True)
    top_apps_list = []
    for ident, data in sorted_apps[:10]:
        dur = data["duration_seconds"]
        pct = round((dur / total_active_seconds * 100), 1) if total_active_seconds > 0 else 0.0
        top_apps_list.append(
            {
                "identifier": ident,
                "category": data["category"],
                "duration_seconds": dur,
                "duration_formatted": format_seconds(dur),
                "percentage": pct,
            }
        )

    # Cache into DailySummary table
    daily_cache = db.query(DailySummary).filter(DailySummary.date == parsed_date).first()
    if not daily_cache:
        daily_cache = DailySummary(
            date=parsed_date,
            total_study_seconds=study_sec,
            total_gaming_seconds=gaming_sec,
            total_distraction_seconds=distract_sec,
            top_distractions=[a for a in top_apps_list if a["category"] == ActivityCategory.ENTERTAINMENT.value],
        )
        db.add(daily_cache)
    else:
        daily_cache.total_study_seconds = study_sec
        daily_cache.total_gaming_seconds = gaming_sec
        daily_cache.total_distraction_seconds = distract_sec
        daily_cache.top_distractions = [a for a in top_apps_list if a["category"] == ActivityCategory.ENTERTAINMENT.value]
    db.commit()

    return {
        "date": date_str,
        "total_active_seconds": total_active_seconds,
        "total_study_seconds": study_sec,
        "total_gaming_seconds": gaming_sec,
        "total_entertainment_seconds": distract_sec,
        "total_unclassified_seconds": unclass_sec,
        "study_hours": round(study_sec / 3600, 2),
        "gaming_hours": round(gaming_sec / 3600, 2),
        "entertainment_hours": round(distract_sec / 3600, 2),
        "study_to_gaming_ratio": ratio_str,
        "categories": categories_list,
        "top_apps": top_apps_list,
    }


def get_distraction_breakdown(
    db: Session, target_date: Union[date, str], limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Identifies non-productive time sinks for a specific date:
    - Filters entertainment sessions.
    - Ranks by duration and computes individual percentage of distraction time.
    """
    date_str = normalize_date(target_date)

    sessions = (
        db.query(ActivitySession)
        .filter(func.date(ActivitySession.start_time) == date_str)
        .filter(ActivitySession.category == ActivityCategory.ENTERTAINMENT.value)
        .all()
    )

    distraction_map: Dict[str, Dict[str, int]] = {}
    total_distraction_sec = 0

    for s in sessions:
        dur = s.duration_seconds
        total_distraction_sec += dur
        ident = s.identifier
        if ident not in distraction_map:
            distraction_map[ident] = {"duration_seconds": 0, "session_count": 0}
        distraction_map[ident]["duration_seconds"] += dur
        distraction_map[ident]["session_count"] += 1

    sorted_distractions = sorted(
        distraction_map.items(), key=lambda x: x[1]["duration_seconds"], reverse=True
    )

    results = []
    for ident, data in sorted_distractions[:limit]:
        dur = data["duration_seconds"]
        pct = (
            round((dur / total_distraction_sec * 100), 1)
            if total_distraction_sec > 0
            else 0.0
        )
        results.append(
            {
                "identifier": ident,
                "duration_seconds": dur,
                "duration_formatted": format_seconds(dur),
                "percentage_of_distraction": pct,
                "session_count": data["session_count"],
            }
        )
    return results


def compare_activity_periods(
    db: Session,
    start_a: str,
    end_a: str,
    start_b: str,
    end_b: str,
) -> Dict[str, Any]:
    """
    Performs comparative trend analysis between two date ranges (e.g., this week vs last week).
    Calculates exact duration deltas and percentage changes for study and gaming.
    """
    def _get_period_metrics(start_str: str, end_str: str, label: str):
        sessions = (
            db.query(ActivitySession)
            .filter(func.date(ActivitySession.start_time) >= start_str)
            .filter(func.date(ActivitySession.start_time) <= end_str)
            .all()
        )

        study_sec = sum(s.duration_seconds for s in sessions if s.category == ActivityCategory.STUDY.value)
        gaming_sec = sum(s.duration_seconds for s in sessions if s.category == ActivityCategory.GAMING.value)

        return {
            "period_label": label,
            "start_date": start_str,
            "end_date": end_str,
            "total_study_seconds": study_sec,
            "total_gaming_seconds": gaming_sec,
            "study_hours": round(study_sec / 3600, 2),
            "gaming_hours": round(gaming_sec / 3600, 2),
        }

    period_a = _get_period_metrics(start_a, end_a, "Period A")
    period_b = _get_period_metrics(start_b, end_b, "Period B")

    study_delta = round(period_a["study_hours"] - period_b["study_hours"], 2)
    gaming_delta = round(period_a["gaming_hours"] - period_b["gaming_hours"], 2)

    study_pct = None
    if period_b["study_hours"] > 0:
        study_pct = round(((period_a["study_hours"] - period_b["study_hours"]) / period_b["study_hours"]) * 100, 1)

    gaming_pct = None
    if period_b["gaming_hours"] > 0:
        gaming_pct = round(((period_a["gaming_hours"] - period_b["gaming_hours"]) / period_b["gaming_hours"]) * 100, 1)

    # Human-readable summary
    study_msg = f"{abs(study_delta)}h {'more' if study_delta >= 0 else 'less'} study"
    gaming_msg = f"{abs(gaming_delta)}h {'more' if gaming_delta >= 0 else 'less'} gaming"
    summary_text = f"In Period A, you had {study_msg} and {gaming_msg} compared to Period B."

    return {
        "period_a": period_a,
        "period_b": period_b,
        "study_delta_hours": study_delta,
        "gaming_delta_hours": gaming_delta,
        "study_change_percent": study_pct,
        "gaming_change_percent": gaming_pct,
        "summary": summary_text,
    }


def get_timeline(db: Session, target_date: Union[date, str]) -> List[Dict[str, Any]]:
    """Returns chronological session blocks for a given date for visual timeline rendering."""
    date_str = normalize_date(target_date)

    sessions = (
        db.query(ActivitySession)
        .filter(func.date(ActivitySession.start_time) == date_str)
        .order_by(ActivitySession.start_time.asc())
        .all()
    )

    timeline = []
    for s in sessions:
        timeline.append(
            {
                "id": s.id,
                "identifier": s.identifier,
                "category": s.category,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration_seconds": s.duration_seconds,
                "duration_formatted": format_seconds(s.duration_seconds),
            }
        )
    return timeline
