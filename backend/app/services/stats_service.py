from datetime import datetime, timedelta, timezone

from ..database import db
from ..database.schemas import READY_STABILITY_DAYS
from ..routers.schemas import DueDay, ProgressDay, ReviewDay
from .review_service import replay_schedule

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
    """Ready cards at the end of each day, oldest first, today last.

    Ready means the same as in the card stats: not due, and not due again before the exam
    of the topic (without an upcoming exam: stability of READY_STABILITY_DAYS or more).
    Past days are recomputed from the review logs, today uses the cards as they are.

    Starts at the first review, which stands in for the creation of the topic or deck (that
    is not stored), and covers at most the last `days` days; without any review it is just
    today. Days are calendar days in the caller's timezone (`tz_offset_minutes` east of
    UTC). None if deck / topic doesnt exist
    """
    offset = timedelta(minutes=tz_offset_minutes)
    now = now or datetime.now(timezone.utc)
    today = (now + offset).date()

    with db() as api:
        cards = api.list_cards(deck_id=deck_id, topic_id=topic_id)
        if cards is None:
            return None
        logs = api.list_review_logs(deck_id=deck_id, topic_id=topic_id) or []
        exam_of_topic = {t.id: t.exam_date for t in api.list_topics()}
        exam_of_deck = {d.id: exam_of_topic.get(d.topic_id) for d in api.list_decks()}

    reviews: dict[int, list[tuple[int, datetime]]] = {}
    for log in logs:  # oldest first
        reviews.setdefault(log.card_id, []).append((log.rating, log.reviewed_at))

    # per card: when it was reviewed and how it was scheduled afterwards
    schedules = []
    for card in cards:
        schedule = replay_schedule(reviews.get(card.id, []))
        if card.last_review is not None:
            # the card itself knows its current schedule exactly
            last_at = schedule[-1][0] if schedule else card.last_review
            schedule[-1:] = [(last_at, card.due, card.stability or 0)]
        exam = exam_of_deck.get(card.deck_id)
        ready_from = None  # with an exam ahead: due at or after this moment = ready
        if exam is not None and exam >= now.date():
            ready_from = datetime(exam.year, exam.month, exam.day, tzinfo=timezone.utc) + timedelta(days=1)
        schedules.append((schedule, ready_from))

    first_day = today - timedelta(days=days - 1)
    if logs:
        first_day = max(first_day, (logs[0].reviewed_at + offset).date())
    else:
        first_day = today

    progress = []
    day = first_day
    while day <= today:
        next_day = day + timedelta(days=1)
        # the moment the day is judged at: its local midnight, or right now for today
        at = min(datetime(next_day.year, next_day.month, next_day.day, tzinfo=timezone.utc) - offset, now)
        ready = 0
        for schedule, ready_from in schedules:
            latest = None
            for entry in schedule:
                if entry[0] > at:
                    break
                latest = entry
            if latest is None or latest[1] <= at:
                continue  # never reviewed, or due again
            if latest[1] >= ready_from if ready_from else latest[2] >= READY_STABILITY_DAYS:
                ready += 1
        progress.append(ProgressDay(date=day, ready=ready))
        day = next_day
    return progress
