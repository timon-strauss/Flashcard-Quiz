from datetime import date, datetime
from pydantic import BaseModel
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
    id: int
    name: str
    exam_date: date | None = None

class TopicStats(BaseModel):
    total_cards: int
    memorized_cards: int
    avg_days_since_seen: float | None = None  # null = empty deck
    days_until_exam: int | None = None        # null = no exam_date

class TopicResponse(BaseModel):
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
    id: int
    name: str
    topic_id: int | None = None

class DeckStats(BaseModel):
    total_cards: int
    memorized_cards: int
    avg_days_since_seen: float | None = None  # null = empty deck

class DeckResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    topic_id: int | None = None
    stats: DeckStats


# ── Cards ─────────────────────────────────────────────────────────────────────

class CardCreate(BaseModel):
    front: str
    back: str
    front_image: str | None = None
    back_image: str | None = None

class CardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    front_image: str | None = None
    back_image: str | None = None

class CardMemorizedUpdate(BaseModel):
    memorized: bool

class CardResponse(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    front_image: str | None = None
    back_image: str | None = None
    memorized: bool
    last_seen_at: datetime | None = None
