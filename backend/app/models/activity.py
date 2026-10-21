from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, JSON, String, Text

from app.db.session import Base


class ActivityEvent(Base):
    """Raw telemetry heartbeat incoming from collectors (Chrome, Desktop, Spotify)."""
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    source = Column(String(50), index=True, nullable=False)  # "desktop", "chrome", "spotify"
    app_or_domain = Column(String(255), index=True, nullable=False)  # "Code.exe", "github.com", "Valorant.exe"
    window_title = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Additional context (e.g., full URL, process path, artist)

    def __repr__(self) -> str:
        return f"<ActivityEvent {self.source} - {self.app_or_domain} at {self.timestamp}>"


class ActivitySession(Base):
    """Aggregated continuous activity session with computed duration and category."""
    __tablename__ = "activity_sessions"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), index=True, nullable=False)
    end_time = Column(DateTime(timezone=True), index=True, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    category = Column(String(50), index=True, nullable=False)  # "study", "gaming", "entertainment", "neutral"
    identifier = Column(String(255), index=True, nullable=False)  # "Code.exe", "youtube.com"
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ActivitySession {self.identifier} ({self.category}) {self.duration_seconds}s>"


class DailySummary(Base):
    """Daily pre-calculated statistics used by deterministic tools and the dashboard."""
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    total_study_seconds = Column(Integer, default=0, nullable=False)
    total_gaming_seconds = Column(Integer, default=0, nullable=False)
    total_distraction_seconds = Column(Integer, default=0, nullable=False)
    top_distractions = Column(JSON, nullable=True)  # List of top distraction apps/sites with durations
    music_summary = Column(JSON, nullable=True)  # Tracks played, total music time

    def __repr__(self) -> str:
        return f"<DailySummary date={self.date} study={self.total_study_seconds}s gaming={self.total_gaming_seconds}s>"

