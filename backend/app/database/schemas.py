from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

# --- topic ---

class TopicBase(BaseModel):
    name: str
    description: str | None = None
    exam_date: date | None = None

class TopicResponse(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class TopicCreate(TopicBase):
    ...

class TopicUpdate(TopicBase):
    id: int
    name: str | None = None


# --- Deck ---

class DeckBase(BaseModel):
    name: str
    description: str | None = None
    topic_id: int | None = None

class DeckResponse(DeckBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class DeckCreate(DeckBase):
    ...

class DeckUpdate(DeckBase):
    id: int
    name: str | None = None
    description: str | None = None


# --- Card ---

class CardBase(BaseModel):
    front: str
    back: str
    front_image: str | None = None
    back_image: str | None = None
    deck_id: int

class CardResponse(CardBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    position: int = 0

    # FSRS scheduling state (read-only here, only changed through CardReview)
    # state: 1 = Learning, 2 = Review, 3 = Relearning (new card = Learning without last_review)
    state: int
    step: int | None = None
    stability: float | None = None
    difficulty: float | None = None
    due: datetime
    last_review: datetime | None = None

class CardCreate(CardBase):
    ...

class CardUpdate(CardBase):
    """Content only. The scheduling state is changed through CardReview."""
    id: int
    front: str | None = None
    back: str | None = None
    deck_id: int | None = None


# --- Review / FSRS ---

class CardReview(BaseModel):
    """One answered card: the rating plus the card state the scheduler computed from it."""
    card_id: int

    # rating: 1 = Again, 2 = Hard, 3 = Good, 4 = Easy
    rating: int
    reviewed_at: datetime

    # new card state after the review
    state: int
    step: int | None = None
    stability: float
    difficulty: float
    due: datetime

class ReviewLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    card_id: int
    rating: int
    reviewed_at: datetime

# Without an upcoming exam a card counts as ready ("gefestigt") once its FSRS stability,
# roughly the interval until the next review, reaches three weeks.
READY_STABILITY_DAYS = 21


class CardStats(BaseModel):
    total: int = 0
    due: int = 0
    # never reviewed
    new: int = 0
    learning: int = 0
    review: int = 0
    relearning: int = 0
    # not due before the exam is over; without an upcoming exam: a long interval
    ready: int = 0
    # most recent review of any card
    last_review: datetime | None = None
