from datetime import datetime, timezone

def parse_timestamp(value: str) -> datetime:
    """
    Parse a timestamp string into an aware UTC datetime.
    Accepts ISO 8601 strings; if parsing fails or the value is empty,
    the current UTC time is returned as a fallback.
    """
    if not value:
        return datetime.now(timezone.utc)

    # Try several common formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    # Fallback: try fromisoformat
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def now_utc_iso() -> str:
    """Return current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()