from datetime import datetime, timedelta, timezone

from ..database import db
from ..routers.schemas import ReviewDay

_RATING_FIELDS = {1: "again", 2: "hard", 3: "good", 4: "easy"}


def review_history(
    days: int,
    deck_id: int | None = None,
    topic_id: int | None = None,
    tz_offset_minutes: int = 0,
    now: datetime | None = None,
) -> list[ReviewDay] | None:
    """Reviews per day for the last `days` days (today included), oldest first.

    Days are calendar days in the caller's timezone (`tz_offset_minutes` east of UTC);
    days without reviews are included with zeros. None if deck / topic doesnt exist
    """
    offset = timedelta(minutes=tz_offset_minutes)
    now = now or datetime.now(timezone.utc)
    today = (now + offset).date()
    first_day = today - timedelta(days=days - 1)
    # local midnight of the first day, expressed in UTC
    since = datetime(first_day.year, first_day.month, first_day.day, tzinfo=timezone.utc) - offset

    with db() as api:
        logs = api.list_review_logs(deck_id=deck_id, topic_id=topic_id, since=since)
    if logs is None:
        return None

    history = {
        first_day + timedelta(days=i): {"total": 0, "again": 0, "hard": 0, "good": 0, "easy": 0}
        for i in range(days)
    }
    for log in logs:
        day = history.get((log.reviewed_at + offset).date())
        if day is None:
            continue
        day["total"] += 1
        day[_RATING_FIELDS[log.rating]] += 1

    return [ReviewDay(date=d, **counts) for d, counts in history.items()]
