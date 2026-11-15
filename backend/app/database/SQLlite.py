from datetime import datetime, timezone

from sqlalchemy import case, func

from . import DatabaseAPI
from .schemas import (
    TopicResponse, TopicCreate, TopicUpdate,
    DeckResponse, DeckCreate, DeckUpdate,
    CardResponse, CardCreate, CardUpdate,
    CardReview, ReviewLogResponse, CardStats,
)
from .models import Topic, Deck, Card, ReviewLog
from .database import SessionLocal, start_db

# FSRS card states
LEARNING, REVIEW, RELEARNING = 1, 2, 3
# Without an upcoming exam a card counts as ready ("gefestigt") once its FSRS stability,
# roughly the interval until the next review, reaches three weeks.
READY_STABILITY_DAYS = 21


# SQLite stores datetimes without timezone, so every stored datetime is UTC by convention.

def _to_db(value: datetime) -> datetime:
    """Aware datetime -> naive UTC. Naive values are taken as UTC already."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _from_db(schema, row):
    """Builds the response and labels its naive datetimes as UTC."""
    response = schema.model_validate(row)
    return response.model_copy(
        update={
            k: v.replace(tzinfo=timezone.utc)
            for k, v in response
            if isinstance(v, datetime) and v.tzinfo is None
        }
    )


def _card_response(row: Card) -> CardResponse:
    return _from_db(CardResponse, row)


class SQLite(DatabaseAPI):
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    @classmethod
    def start_db(cls):
        start_db()

    def _in_scope(self, query, deck_id: int | None, topic_id: int | None):
        """Restricts a Card query to a deck and/or topic. None if one of them doesnt exist."""
        if deck_id is not None:
            if self.db.get(Deck, deck_id) is None:
                return None
            query = query.filter(Card.deck_id == deck_id)
        if topic_id is not None:
            if self.db.get(Topic, topic_id) is None:
                return None
            query = query.join(Deck, Card.deck_id == Deck.id).filter(Deck.topic_id == topic_id)
        return query

    # --- topic ---

    def list_topics(self) -> list[TopicResponse]:
        rows = self.db.query(Topic).all()
        return [TopicResponse.model_validate(r) for r in rows]

    def get_topic(self, topic_id: int) -> TopicResponse | None:
        row = self.db.get(Topic, topic_id)
        if row is None:
            return None
        return TopicResponse.model_validate(row)

    def create_topic(self, create_topic: TopicCreate) -> TopicResponse:
        row = Topic(**create_topic.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return TopicResponse.model_validate(row)

    def update_topic(self, update_topic: TopicUpdate) -> TopicResponse | None:
        row = self.db.get(Topic, update_topic.id)
        if row is None:
            return None
        for key, value in update_topic.model_dump(exclude_unset=True, exclude={"id"}).items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return TopicResponse.model_validate(row)

    def delete_topic(self, topic_id: int) -> bool:
        row = self.db.get(Topic, topic_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    # --- Decks ---

    def list_decks(
        self, topic_id: int | None = None, without_topic: bool = False
    ) -> list[DeckResponse] | None:
        query = self.db.query(Deck)
        if without_topic:
            query = query.filter(Deck.topic_id.is_(None))
        if topic_id is not None:
            if self.db.get(Topic, topic_id) is None:
                return None
            query = query.filter(Deck.topic_id == topic_id)
        return [DeckResponse.model_validate(r) for r in query.all()]

    def get_deck(self, deck_id: int) -> DeckResponse | None:
        row = self.db.get(Deck, deck_id)
        if row is None:
            return None
        return DeckResponse.model_validate(row)

    def create_deck(self, create_deck: DeckCreate) -> DeckResponse | None:
        if create_deck.topic_id is not None and self.db.get(Topic, create_deck.topic_id) is None:
            return None
        row = Deck(**create_deck.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return DeckResponse.model_validate(row)

    def update_deck(self, update_deck: DeckUpdate) -> DeckResponse | None:
        row = self.db.get(Deck, update_deck.id)
        if row is None:
            return None
        for key, value in update_deck.model_dump(exclude_unset=True, exclude={"id"}).items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return DeckResponse.model_validate(row)

    def delete_deck(self, deck_id: int) -> bool:
        row = self.db.get(Deck, deck_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    # --- Cards ---

    def list_cards(self, deck_id: int | None = None) -> list[CardResponse] | None:
        query = self._in_scope(self.db.query(Card), deck_id, None)
        if query is None:
            return None
        rows = query.order_by(Card.deck_id, Card.position, Card.id).all()
        return [_card_response(r) for r in rows]

    def get_card(self, card_id: int) -> CardResponse | None:
        row = self.db.get(Card, card_id)
        if row is None:
            return None
        return _card_response(row)

    def create_card(self, create_card: CardCreate) -> CardResponse | None:
        if self.db.get(Deck, create_card.deck_id) is None:
            return None
        count = self.db.query(Card).filter(Card.deck_id == create_card.deck_id).count()
        row = Card(
            **create_card.model_dump(),
            position=count,
            state=LEARNING,
            step=0,
            due=_to_db(datetime.now(timezone.utc)),  # new cards are due immediately
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _card_response(row)

    def update_card(self, update_card: CardUpdate) -> CardResponse | None:
        row = self.db.get(Card, update_card.id)
        if row is None:
            return None
        for key, value in update_card.model_dump(exclude_unset=True, exclude={"id"}).items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return _card_response(row)

    def delete_card(self, card_id: int) -> bool:
        row = self.db.get(Card, card_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def reorder_cards(self, deck_id: int, card_ids: list[int]) -> list[CardResponse] | None:
        if self.db.get(Deck, deck_id) is None:
            return None
        for pos, card_id in enumerate(card_ids):
            row = self.db.get(Card, card_id)
            if row and row.deck_id == deck_id:
                row.position = pos
        self.db.commit()
        return self.list_cards(deck_id=deck_id)

    # --- Reviews / FSRS ---

    def review_card(self, review: CardReview) -> CardResponse | None:
        row = self.db.get(Card, review.card_id)
        if row is None:
            return None
        reviewed_at = _to_db(review.reviewed_at)

        row.state = review.state
        row.step = review.step
        row.stability = review.stability
        row.difficulty = review.difficulty
        row.due = _to_db(review.due)
        row.last_review = reviewed_at
        self.db.add(
            ReviewLog(
                card_id=row.id,
                rating=review.rating,
                reviewed_at=reviewed_at,
            )
        )
        self.db.commit()  # card state and log are written together
        self.db.refresh(row)
        return _card_response(row)

    def list_due_cards(
        self,
        due_before: datetime,
        deck_id: int | None = None,
        topic_id: int | None = None,
        limit: int | None = None,
    ) -> list[CardResponse] | None:
        query = self._in_scope(self.db.query(Card), deck_id, topic_id)
        if query is None:
            return None
        query = query.filter(Card.due <= _to_db(due_before)).order_by(Card.due, Card.id)
        if limit is not None:
            query = query.limit(limit)
        return [_card_response(r) for r in query.all()]

    def list_review_logs(
        self,
        card_id: int | None = None,
        deck_id: int | None = None,
        topic_id: int | None = None,
        since: datetime | None = None,
    ) -> list[ReviewLogResponse] | None:
        query = self.db.query(ReviewLog)
        if card_id is not None:
            if self.db.get(Card, card_id) is None:
                return None
            query = query.filter(ReviewLog.card_id == card_id)
        if deck_id is not None or topic_id is not None:
            query = self._in_scope(
                query.join(Card, ReviewLog.card_id == Card.id), deck_id, topic_id
            )
            if query is None:
                return None
        if since is not None:
            query = query.filter(ReviewLog.reviewed_at >= _to_db(since))
        rows = query.order_by(ReviewLog.reviewed_at, ReviewLog.id).all()
        return [_from_db(ReviewLogResponse, r) for r in rows]

    def get_card_stats(
        self,
        due_before: datetime,
        deck_id: int | None = None,
        topic_id: int | None = None,
    ) -> CardStats | None:
        def count_if(condition):
            return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)

        if deck_id is not None and self.db.get(Deck, deck_id) is None:
            return None
        if topic_id is not None and self.db.get(Topic, topic_id) is None:
            return None

        now = _to_db(due_before)
        is_new = (Card.state == LEARNING) & Card.last_review.is_(None)
        is_due = Card.due <= now
        # Ready = nothing left to do before the exam: the card is not due and will not
        # become due until the exam day is over. Without an upcoming exam (no topic, no
        # exam date, exam already written) a long interval counts instead.
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        exam_ahead = Topic.exam_date.is_not(None) & (Topic.exam_date >= today)
        is_ready = ~is_due & case(
            (exam_ahead, func.datetime(Card.due) >= func.datetime(Topic.exam_date, "+1 day")),
            else_=func.coalesce(Card.stability, 0) >= READY_STABILITY_DAYS,
        )

        query = (
            self.db.query(
                func.count(Card.id),
                count_if(is_due),
                count_if(is_new),
                count_if((Card.state == LEARNING) & Card.last_review.is_not(None)),
                count_if(Card.state == REVIEW),
                count_if(Card.state == RELEARNING),
                count_if(is_ready),
                func.max(Card.last_review),
            )
            .select_from(Card)
            .join(Deck, Card.deck_id == Deck.id)
            .outerjoin(Topic, Deck.topic_id == Topic.id)
        )
        if deck_id is not None:
            query = query.filter(Card.deck_id == deck_id)
        if topic_id is not None:
            query = query.filter(Deck.topic_id == topic_id)

        total, due, new, learning, review, relearning, ready, last_review = query.one()
        return CardStats(
            total=total, due=due, new=new,
            learning=learning, review=review, relearning=relearning,
            ready=ready,
            last_review=last_review.replace(tzinfo=timezone.utc) if last_review else None,
        )
