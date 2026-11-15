from datetime import datetime, timezone

from fsrs import Scheduler, Card, Rating, State

from ..database import db
from ..database.schemas import CardReview as DbCardReview, CardResponse as DbCardResponse
from ..routers.schemas import CardResponse

# FSRS with its default parameters, 90 % desired retention
scheduler = Scheduler()


def _to_fsrs_card(card: DbCardResponse) -> Card:
    return Card(
        card_id=card.id,
        state=State(card.state),
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        last_review=card.last_review,
    )


def review_card(card_id: int, rating: int, now: datetime | None = None) -> CardResponse | None:
    """Rates a card (1 = Again, 2 = Hard, 3 = Good, 4 = Easy) and schedules its next review.

    None if card doesnt exist
    """
    now = now or datetime.now(timezone.utc)
    with db() as api:
        card = api.get_card(card_id)
        if card is None:
            return None
        scheduled, _ = scheduler.review_card(_to_fsrs_card(card), Rating(rating), now)
        updated = api.review_card(DbCardReview(
            card_id=card_id,
            rating=rating,
            reviewed_at=now,
            state=scheduled.state.value,
            step=scheduled.step,
            stability=scheduled.stability,
            difficulty=scheduled.difficulty,
            due=scheduled.due,
        ))
    if updated is None:
        return None
    return CardResponse.model_validate(updated)


def list_due_cards(
    deck_id: int | None = None,
    topic_id: int | None = None,
    limit: int | None = None,
    now: datetime | None = None,
) -> list[CardResponse] | None:
    """Cards to study now, most overdue first. None if deck / topic doesnt exist"""
    now = now or datetime.now(timezone.utc)
    with db() as api:
        cards = api.list_due_cards(now, deck_id=deck_id, topic_id=topic_id, limit=limit)
    if cards is None:
        return None
    return [CardResponse.model_validate(c) for c in cards]
