"""
Helpers
-------
Small formatting utilities shared across pages.
"""

from datetime import datetime


def format_timestamp(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%b %d, %Y · %I:%M %p")
    except Exception:
        return iso_string or "—"


def pct_delta_str(current: float, previous: float) -> str | None:
    """Returns a display string like '+7%' or None if there's nothing to show."""
    if previous is None:
        return None
    diff = round(current - previous, 1)
    if diff == 0:
        return None
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff}%"


def count_delta_str(current: int, previous: int) -> str | None:
    diff = current - previous
    if diff == 0:
        return None
    return f"+{diff}" if diff > 0 else str(diff)
