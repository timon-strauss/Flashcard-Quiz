from datetime import datetime, timedelta, timezone

from ..database import db
from ..routers.schemas import DueDay, ProgressDay, ReviewDay

_RATING_FIELDS = {1: "again", 2: "hard", 3: "good", 4: "easy"}
_KNOWN_RATINGS = {3, 4}  # Good, Easy


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


def due_forecast(
    days: int,
    deck_id: int | None = None,
    topic_id: int | None = None,
    tz_offset_minutes: int = 0,
    now: datetime | None = None,
) -> list[DueDay] | None:
    """Cards becoming due per day for the next `days` days (today included), soonest first.

    Days are calendar days in the caller's timezone (`tz_offset_minutes` east of UTC).
    Overdue cards count towards today; days without due cards are included with zero.
    None if deck / topic doesnt exist
    """
    offset = timedelta(minutes=tz_offset_minutes)
    now = now or datetime.now(timezone.utc)
    today = (now + offset).date()
    after_last_day = today + timedelta(days=days)
    # local midnight after the last day, expressed in UTC
    until = datetime(
        after_last_day.year, after_last_day.month, after_last_day.day, tzinfo=timezone.utc
    ) - offset

    with db() as api:
        cards = api.list_due_cards(until, deck_id=deck_id, topic_id=topic_id)
    if cards is None:
        return None

    forecast = {today + timedelta(days=i): 0 for i in range(days)}
    for card in cards:
        day = max((card.due + offset).date(), today)
        if day in forecast:  # a card due exactly at `until` belongs to the day after
            forecast[day] += 1

    return [DueDay(date=d, count=count) for d, count in forecast.items()]


def progress_history(
    days: int,
    deck_id: int | None = None,
    topic_id: int | None = None,
    tz_offset_minutes: int = 0,
    now: datetime | None = None,
) -> list[ProgressDay] | None:
    """Known cards at the end of each of the last `days` days (today included), oldest first.

    A card is known while its most recent rating is Good or Easy, so the count drops when a
    card is rated Again or Hard and recovers once it is rated Good again. Days are calendar
    days in the caller's timezone (`tz_offset_minutes` east of UTC).
    None if deck / topic doesnt exist
    """
    offset = timedelta(minutes=tz_offset_minutes)
    today = ((now or datetime.now(timezone.utc)) + offset).date()
    first_day = today - timedelta(days=days - 1)

    with db() as api:
        # all logs, oldest first: ratings from before the window still decide where it starts
        logs = api.list_review_logs(deck_id=deck_id, topic_id=topic_id)
    if logs is None:
        return None

    known_cards: set[int] = set()
    progress = []
    position = 0
    for i in range(days):
        day = first_day + timedelta(days=i)
        while position < len(logs) and (logs[position].reviewed_at + offset).date() <= day:
            log = logs[position]
            if log.rating in _KNOWN_RATINGS:
                known_cards.add(log.card_id)
            else:
                known_cards.discard(log.card_id)
            position += 1
        progress.append(ProgressDay(date=day, known=len(known_cards)))
    return progress
