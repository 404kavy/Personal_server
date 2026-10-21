from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import ActivityEvent, ActivitySession, CategoryRule
from app.schemas.activity import ActivityCategory

# Baseline Fallback Keywords (Used only when no user-defined rule exists)
DEFAULT_STUDY_IDENTIFIERS = {
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

DEFAULT_GAMING_IDENTIFIERS = {
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

DEFAULT_DISTRACTION_IDENTIFIERS = {
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


def classify_activity(db: Session, identifier: str, window_title: Optional[str] = None) -> str:
    """
    Classifies an application or domain:
    1. Checks user-defined rules in `category_rules` table first (User rules ALWAYS take precedence).
    2. If no user rule matches, checks default baseline keywords.
    3. If still unmatched, marks as 'unclassified' so it appears in the user's UI Inbox for one-click tagging.
    """
    ident_lower = identifier.lower().strip()

    # Step 1: Check User-defined rules from database
    user_rules = db.query(CategoryRule).all()
    for rule in user_rules:
        rule_pattern = rule.pattern.lower().strip()
        if ident_lower == rule_pattern or ident_lower.endswith(rule_pattern):
            return rule.category

    # Step 2: Fallback baseline keywords
    if ident_lower in DEFAULT_STUDY_IDENTIFIERS:
        return ActivityCategory.STUDY.value

    if ident_lower in DEFAULT_GAMING_IDENTIFIERS:
        return ActivityCategory.GAMING.value

    if ident_lower in DEFAULT_DISTRACTION_IDENTIFIERS:
        return ActivityCategory.ENTERTAINMENT.value

    for site in DEFAULT_DISTRACTION_IDENTIFIERS:
        if ident_lower.endswith(site):
            return ActivityCategory.ENTERTAINMENT.value

    for site in DEFAULT_STUDY_IDENTIFIERS:
        if ident_lower.endswith(site):
            return ActivityCategory.STUDY.value

    # Step 3: Unmatched -> unclassified (Appears in UI for user tagging)
    return ActivityCategory.UNCLASSIFIED.value


def process_event_into_session(db: Session, event: ActivityEvent) -> ActivitySession:
    """
    Consolidates contiguous telemetry heartbeats into continuous time blocks.
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
            # Different app or long gap: close previous session
            active_session.is_active = False
            db.commit()

    # Create new session with user-first classification
    category = classify_activity(db, event.app_or_domain, event.window_title)
    new_session = ActivitySession(
        start_time=event.timestamp,
        end_time=event.timestamp,
        duration_seconds=0,
        category=category,
        identifier=event.app_or_domain,
        is_active=True,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def save_user_rule_and_retroactively_tag(
    db: Session, pattern: str, category: str, apply_to_past: bool = True
) -> CategoryRule:
    """
    Creates or updates a user-defined category rule in the database.
    If apply_to_past is True, updates all historical sessions matching this pattern.
    """
    clean_pattern = pattern.lower().strip()
    clean_category = category.lower().strip()

    rule = db.query(CategoryRule).filter(func.lower(CategoryRule.pattern) == clean_pattern).first()
    if rule:
        rule.category = clean_category
    else:
        rule = CategoryRule(pattern=clean_pattern, category=clean_category)
        db.add(rule)

    db.commit()
    db.refresh(rule)

    if apply_to_past:
        # Retroactively reclassify all existing sessions matching this pattern
        matching_sessions = (
            db.query(ActivitySession)
            .filter(func.lower(ActivitySession.identifier) == clean_pattern)
            .all()
        )
        for s in matching_sessions:
            s.category = clean_category
        db.commit()

    return rule


def get_unclassified_apps_summary(db: Session) -> List[Dict]:
    """
    Aggregates all applications and domains that are currently 'unclassified'
    so the UI can display an 'Unclassified Inbox' for one-click tagging.
    """
    results = (
        db.query(
            ActivitySession.identifier,
            func.sum(ActivitySession.duration_seconds).label("total_seconds"),
            func.count(ActivitySession.id).label("session_count"),
        )
        .filter(ActivitySession.category == ActivityCategory.UNCLASSIFIED.value)
        .group_by(ActivitySession.identifier)
        .order_by(func.sum(ActivitySession.duration_seconds).desc())
        .all()
    )

    unclassified_list = []
    for r in results:
        # Grab a sample window title from recent events for user reference
        sample_event = (
            db.query(ActivityEvent.window_title)
            .filter(func.lower(ActivityEvent.app_or_domain) == r.identifier.lower())
            .filter(ActivityEvent.window_title.isnot(None))
            .order_by(ActivityEvent.timestamp.desc())
            .first()
        )
        unclassified_list.append(
            {
                "identifier": r.identifier,
                "total_duration_seconds": r.total_seconds or 0,
                "session_count": r.session_count,
                "sample_window_title": sample_event[0] if sample_event else None,
            }
        )

    return unclassified_list
