from datetime import datetime

def get_datetime_utc() -> datetime:
    """Get current UTC datetime"""
    from datetime import timezone
    return datetime.now(timezone.utc)