from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import verify_local_token
from app.db.session import get_db
from app.models.activity import ActivityEvent, ActivitySession
from app.schemas.activity import (
    ActivityCategory,
    ActivityEventResponse,
    ActivitySessionResponse,
    EventIngestRequest,
    EventIngestResponse,
)
from app.services.session_service import process_event_into_session

router = APIRouter(prefix="/events", tags=["Telemetry Ingestion"])


@router.post(
    "/ingest",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a telemetry event from a collector",
)
async def ingest_event(
    payload: EventIngestRequest,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_local_token),
):
    """
    Ingests a raw telemetry heartbeat from a collector:
    - Saves the raw event in `activity_events`.
    - Automatically consolidates contiguous heartbeats into an `ActivitySession`.
    - Categorizes into 'study', 'gaming', 'entertainment', or 'neutral'.
    """
    event_timestamp = payload.client_timestamp or datetime.now(timezone.utc)

    # 1. Record raw event
    event = ActivityEvent(
        timestamp=event_timestamp,
        source=payload.source.value,
        app_or_domain=payload.app_or_domain,
        window_title=payload.window_title,
        metadata_json=payload.metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 2. Process into session
    session = process_event_into_session(db, event)

    return EventIngestResponse(
        status="recorded",
        event_id=event.id,
        timestamp=event.timestamp,
        session_id=session.id,
        session_category=ActivityCategory(session.category),
    )


@router.get(
    "/recent",
    response_model=List[ActivityEventResponse],
    summary="Get recent raw telemetry events",
)
async def get_recent_events(
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = Query(None, description="Filter by source (desktop, chrome, spotify)"),
    db: Session = Depends(get_db),
):
    """Returns recent raw activity events for debugging and collector verification."""
    query = db.query(ActivityEvent).order_by(ActivityEvent.timestamp.desc())
    if source:
        query = query.filter(ActivityEvent.source == source)
    return query.limit(limit).all()


@router.get(
    "/sessions",
    response_model=List[ActivitySessionResponse],
    summary="Get consolidated activity sessions",
)
async def get_sessions(
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False, description="Filter to only the currently active session"),
    db: Session = Depends(get_db),
):
    """Returns contiguous activity sessions with duration and classification."""
    query = db.query(ActivitySession).order_by(ActivitySession.end_time.desc())
    if active_only:
        query = query.filter(ActivitySession.is_active == True)
    return query.limit(limit).all()

