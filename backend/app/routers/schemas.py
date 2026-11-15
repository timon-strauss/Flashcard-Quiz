from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from fastapi import HTTPException


def _not_implemented():
    raise HTTPException(status_code=501, detail="Endpoint not yet implemented")


# ── Topics ────────────────────────────────────────────────────────────────────

class TopicCreate(BaseModel):
    name: str
    description: str | None = None
    exam_date: date | None = None

class TopicUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    exam_date: date | None = None

class TopicLean(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    exam_date: date | None = None

class TopicStats(BaseModel):
    total_cards: int
    due_cards: int
    new_cards: int         # never reviewed
    learning_cards: int
    review_cards: int
    relearning_cards: int
    days_until_exam: int | None = None  # null = no exam_date

class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    exam_date: date | None = None
    stats: TopicStats


# ── Decks ─────────────────────────────────────────────────────────────────────

class DeckCreate(BaseModel):
    name: str
    description: str | None = None
    topic_id: int | None = None

class DeckUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    topic_id: int | None = None

class DeckLean(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    topic_id: int | None = None

class DeckStats(BaseModel):
    total_cards: int
    due_cards: int
    new_cards: int         # never reviewed
    learning_cards: int
    review_cards: int
    relearning_cards: int

class DeckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    topic_id: int | None = None
    stats: DeckStats


# ── Cards ─────────────────────────────────────────────────────────────────────

class CardCreate(BaseModel):
    deck_id: int
    front: str
    back: str
    front_image: str | None = None
    back_image: str | None = None

class CardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    front_image: str | None = None
    back_image: str | None = None

class CardReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=4)  # 1 = Again, 2 = Hard, 3 = Good, 4 = Easy

class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deck_id: int
    front: str
    back: str
    front_image: str | None = None
    back_image: str | None = None
    position: int = 0

    # FSRS scheduling state
    state: int  # 1 = Learning, 2 = Review, 3 = Relearning
    step: int | None = None
    stability: float | None = None
    difficulty: float | None = None
    due: datetime
    last_review: datetime | None = None  # null = new card


class CardOrderUpdate(BaseModel):
    order: list[int]  # list of card IDs in desired order


# ── Stats ─────────────────────────────────────────────────────────────────────

class ReviewDay(BaseModel):
    date: date
    total: int
    again: int
    hard: int
    good: int
    easy: int
