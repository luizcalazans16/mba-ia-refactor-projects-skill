from datetime import datetime, timezone


def utcnow():
    """Agora em UTC, sem tzinfo — o mesmo formato que o SQLite já armazena (substitui datetime.utcnow, deprecated)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
