from abc import ABC, abstractmethod
from .schemas import TopicResponse, TopicUpdate, TopicCreate, DeckResponse, DeckUpdate, DeckCreate, CardResponse, CardUpdate, CardCreate


class DatabaseAPI(ABC):

    @classmethod
    @abstractmethod
    def start_db(cls):
        ...

    # --- topic ---
    @abstractmethod
    def list_topics(self) -> list[TopicResponse]:
        ...

    @abstractmethod
    def get_topic(self, topic_id: int) -> TopicResponse | None:
        ...

    @abstractmethod
    def create_topics(self, create_topic: TopicCreate) -> TopicResponse:
        ...

    @abstractmethod
    def update_topics(self, update_topic: TopicUpdate) -> TopicResponse | None:
        ...

    @abstractmethod
    def delete_topic(self, topic_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        ...


    # --- Decks ---

    @abstractmethod
    def list_decks(self) -> list[DeckResponse]:
        ...

    @abstractmethod
    def list_decks_by_topic(self, topic_id) -> list[DeckResponse] | None:
        """None if topic doesnt exist"""
        ...

    @abstractmethod
    def get_deck(self, deck_id: int) -> DeckResponse | None:
        ...

    @abstractmethod
    def create_deck(self, create_deck: DeckCreate) -> DeckResponse | None:
        """None if topic doesnt exist"""
        ...

    @abstractmethod
    def update_deck(self, update_deck: DeckUpdate) -> DeckResponse | None:
        ...

    @abstractmethod
    def delete_deck(self, deck_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        ...

    # --- Cards ---

    @abstractmethod
    def list_cards(self) -> list[CardResponse]:
        ...
    @abstractmethod
    def list_cards_by_deck(self, deck_id: id) -> list[CardResponse] | None:
        """None if deck doesnt exist"""
        ...

    @abstractmethod
    def list_cards_by_topic(self, topic_id: id) -> list[CardResponse] | None:
        """None if topic doesnt exist"""
        ...

    @abstractmethod
    def get_card(self, card_id: int) -> CardResponse | None:
        ...

    @abstractmethod
    def create_card( self, create_card: CardCreate) -> CardResponse | None:
        """None if deck doesnt exist"""
        ...

    @abstractmethod
    def update_card( self, create_update: CardUpdate) -> CardResponse | None:
        ...

    @abstractmethod
    def delete_card(self, card_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        ...


from .sqlliteAPI import SQLiteAPI

db: type[DatabaseAPI] = SQLiteAPI

