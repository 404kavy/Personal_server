from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.activity import ActivityEvent, ActivitySession
from app.schemas.activity import ActivityCategory

# Classification keywords & rules
STUDY_IDENTIFIERS = {
    # Coding & Development Apps
    "code.exe",
    "cursor.exe",
    "pycharm64.exe",
    "idea64.exe",
    "devenv.exe",
    "windowsterminal.exe",
    "powershell.exe",
    "cmd.exe",
    "nvim.exe",
    "sublime_text.exe",
    "obsidian.exe",
    # Documentation & Academic Domains
    "github.com",
    "gitlab.com",
    "stackoverflow.com",
    "docs.python.org",
    "fastapi.tiangolo.com",
    "developer.mozilla.org",
    "arxiv.org",
    "coursera.org",
    "udemy.com",
    "leetcode.com",
    "claude.ai",
    "chatgpt.com",
}

GAMING_IDENTIFIERS = {
    "valorant.exe",
    "cs2.exe",
    "csgo.exe",
    "dota2.exe",
    "league of legends.exe",
    "riotclientservices.exe",
    "steam.exe",
    "epicgameslauncher.exe",
    "gta5.exe",
    "minecraft.exe",
    "overwatch.exe",
    "fortniteclient-win64-shipping.exe",
}

DISTRACTION_IDENTIFIERS = {
    # Entertainment & Social Media
    "youtube.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "netflix.com",
    "twitch.tv",
    "facebook.com",
    "discord.exe",
}


def classify_activity(identifier: str, window_title: Optional[str] = None) -> ActivityCategory:
    """Classifies an app or domain into study, gaming, entertainment, or neutral."""
    ident_lower = identifier.lower().strip()

    if ident_lower in STUDY_IDENTIFIERS:
        return ActivityCategory.STUDY

    if ident_lower in GAMING_IDENTIFIERS:
        return ActivityCategory.GAMING

    if ident_lower in DISTRACTION_IDENTIFIERS:
        return ActivityCategory.ENTERTAINMENT

    # Check for domain suffix matches (e.g., sub.youtube.com or www.reddit.com)
    for site in DISTRACTION_IDENTIFIERS:
        if ident_lower.endswith(site):
            return ActivityCategory.ENTERTAINMENT

    for site in STUDY_IDENTIFIERS:
        if ident_lower.endswith(site):
            return ActivityCategory.STUDY

    return ActivityCategory.NEUTRAL


def process_event_into_session(db: Session, event: ActivityEvent) -> ActivitySession:
    """
    Session consolidation algorithm:
    Groups contiguous heartbeats into continuous time blocks.
    - If the same application/domain is active within 60s, extends the current session.
    - If inactive for >60s or application changes, finalizes previous session and starts a new one.
    """
    # Look for the currently active session
    active_session = (
        db.query(ActivitySession)
        .filter(ActivitySession.is_active == True)
        .order_by(ActivitySession.end_time.desc())
        .first()
    )

    event_time = event.timestamp
    # Make sure event_time has tzinfo for difference calculation
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)

    if active_session:
        session_end = active_session.end_time
        if session_end.tzinfo is None:
            session_end = session_end.replace(tzinfo=timezone.utc)

        time_gap = (event_time - session_end).total_seconds()

        # If heartbeats are contiguous (<= 60s gap) and identifier is identical: extend session
        if 0 <= time_gap <= 60 and active_session.identifier.lower() == event.app_or_domain.lower():
            active_session.end_time = event.timestamp
            start_tz = active_session.start_time
            if start_tz.tzinfo is None:
                start_tz = start_tz.replace(tzinfo=timezone.utc)
            active_session.duration_seconds = max(1, int((event_time - start_tz).total_seconds()))
            db.commit()
            db.refresh(active_session)
            return active_session
        else:
            # Different app or long gap: close active session
            active_session.is_active = False
            db.commit()

    # Create new session
    category = classify_activity(event.app_or_domain, event.window_title)
    new_session = ActivitySession(
        start_time=event.timestamp,
        end_time=event.timestamp,
        duration_seconds=0,
        category=category.value,
        identifier=event.app_or_domain,
        is_active=True,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session
