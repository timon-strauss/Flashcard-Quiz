from datetime import date, datetime
from pydantic import BaseModel

# --- topic ---

class topicBase(BaseModel):
    name: str 
    description: str | None = None
    exam_date: date | None = None

class topicResponse(topicBase):
    id: int

class topicCreate(topicBase):
    pass

class topicUpdate(topicBase):
    id: int
    name: str | None = None


# --- Deck ---

class deckBase(BaseModel):
    name: str
    description: str | None = None
    topic_id: int | None = None

class deckResponse(deckBase):
    id: int

class deckCreate(deckBase):
    pass

class deckUpdate(deckBase):
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
    id: int
    memorized: bool = False
    last_seen_at: datetime | None = None

class CardCreate(CardBase):
    pass

class CardUpdate(CardBase):
    id: int
    front: str | None = None
    back: str | None = None
    memorized: bool | None = None
    last_seen_at: datetime | None = None
    deck_id: int | None = None
