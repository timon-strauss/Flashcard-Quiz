from . import DatabaseAPI
from .schemas import (
    TopicResponse, TopicCreate, TopicUpdate,
    DeckResponse, DeckCreate, DeckUpdate,
    CardResponse, CardCreate, CardUpdate,
)
from .models import Topic, Deck, Card
from .database import SessionLocal, start_db


class SQLiteAPI(DatabaseAPI):
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    @classmethod
    def start_db(cls):
        start_db()

    # --- topic ---

    def list_topics(self) -> list[TopicResponse]:
        rows = self.db.query(Topic).all()
        return [TopicResponse.model_validate(r) for r in rows]

    def get_topic(self, topic_id: int) -> TopicResponse | None:
        row = self.db.get(Topic, topic_id)
        if row is None:
            return None
        return TopicResponse.model_validate(row)

    def create_topics(self, create_topic: TopicCreate) -> TopicResponse:
        row = Topic(**create_topic.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return TopicResponse.model_validate(row)

    def update_topics(self, update_topic: TopicUpdate) -> TopicResponse | None:
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

    def list_decks(self) -> list[DeckResponse]:
        rows = self.db.query(Deck).all()
        return [DeckResponse.model_validate(r) for r in rows]

    def list_decks_by_topic(self, topic_id) -> list[DeckResponse] | None:
        if self.db.get(Topic, topic_id) is None:
            return None
        rows = self.db.query(Deck).filter(Deck.topic_id == topic_id).all()
        return [DeckResponse.model_validate(r) for r in rows]

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

    def list_cards(self) -> list[CardResponse]:
        rows = self.db.query(Card).all()
        return [CardResponse.model_validate(r) for r in rows]

    def list_cards_by_deck(self, deck_id: id) -> list[CardResponse] | None:
        if self.db.get(Deck, deck_id) is None:
            return None
        rows = self.db.query(Card).filter(Card.deck_id == deck_id).all()
        return [CardResponse.model_validate(r) for r in rows]

    def list_cards_by_topic(self, topic_id: id) -> list[CardResponse] | None:
        if self.db.get(Topic, topic_id) is None:
            return None
        rows = (
            self.db.query(Card)
            .join(Deck, Card.deck_id == Deck.id)
            .filter(Deck.topic_id == topic_id)
            .all()
        )
        return [CardResponse.model_validate(r) for r in rows]

    def get_card(self, card_id: int) -> CardResponse | None:
        row = self.db.get(Card, card_id)
        if row is None:
            return None
        return CardResponse.model_validate(row)

    def create_card(self, create_card: CardCreate) -> CardResponse | None:
        if self.db.get(Deck, create_card.deck_id) is None:
            return None
        row = Card(**create_card.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return CardResponse.model_validate(row)

    def update_card(self, create_update: CardUpdate) -> CardResponse | None:
        row = self.db.get(Card, create_update.id)
        if row is None:
            return None
        for key, value in create_update.model_dump(exclude_unset=True, exclude={"id"}).items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return CardResponse.model_validate(row)

    def delete_card(self, card_id: int) -> bool:
        row = self.db.get(Card, card_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True
