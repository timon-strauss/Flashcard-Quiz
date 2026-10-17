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
    pass

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
    pass

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
