from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DeckBase(BaseModel):
    name: str
    description: str | None = None


class DeckCreate(DeckBase):
    pass


class DeckUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DeckRead(DeckBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CardBase(BaseModel):
    front: str
    back: str


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None


class CardRead(CardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deck_id: int
    created_at: datetime
