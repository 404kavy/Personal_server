from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventSource(str, Enum):
    DESKTOP = "desktop"
    CHROME = "chrome"
    SPOTIFY = "spotify"


class ActivityCategory(str, Enum):
    STUDY = "study"
    GAMING = "gaming"
    ENTERTAINMENT = "entertainment"
    NEUTRAL = "neutral"
    UNCLASSIFIED = "unclassified"


class EventIngestRequest(BaseModel):
    """Payload sent by telemetry collectors (Desktop Watcher, Chrome Extension, Spotify Sync)."""
    source: EventSource = Field(..., description="Source of the event: desktop, chrome, or spotify")
    app_or_domain: str = Field(..., min_length=1, max_length=255, description="Process name or URL domain")
    window_title: Optional[str] = Field(None, description="Active window title or tab title")
    client_timestamp: Optional[datetime] = Field(None, description="Timestamp from client; defaults to server UTC if omitted")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context (URL path, artist, track, etc.)")


class EventIngestResponse(BaseModel):
    """Response returned upon successful ingestion."""
    status: str = "recorded"
    event_id: int
    timestamp: datetime
    session_id: Optional[int] = None
    session_category: Optional[str] = None


class ActivityEventResponse(BaseModel):
    """Serialized activity event."""
    id: int
    timestamp: datetime
    source: str
    app_or_domain: str
    window_title: Optional[str]
    metadata_json: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ActivitySessionResponse(BaseModel):
    """Serialized activity session."""
    id: int
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    category: str
    identifier: str
    is_active: bool

    class Config:
        from_attributes = True


class DailySummaryResponse(BaseModel):
    """Aggregated daily analytics summary."""
    id: int
    date: date
    total_study_seconds: int
    total_gaming_seconds: int
    total_distraction_seconds: int
    top_distractions: Optional[List[Dict[str, Any]]] = None
    music_summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# --- User-Defined Classification Rules & Unclassified App Inbox ---

class CategoryRuleCreate(BaseModel):
    """Payload for creating or updating a user-defined classification rule."""
    pattern: str = Field(..., min_length=1, max_length=255, description="Process name or domain (e.g. 'blender.exe', 'reddit.com')")
    category: str = Field(..., min_length=1, max_length=50, description="Target category: study, gaming, entertainment, neutral, or custom")
    apply_to_past: bool = Field(True, description="Whether to retroactively update past sessions with this identifier")


class CategoryRuleResponse(BaseModel):
    """Serialized user category rule."""
    id: int
    pattern: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


class UnclassifiedAppResponse(BaseModel):
    """An app or website that has been recorded but does not yet have a user rule."""
    identifier: str
    total_duration_seconds: int
    session_count: int
    sample_window_title: Optional[str] = None
