from abc import ABC, abstractmethod
from .schemas import topicResponse, topicUpdate, topicCreate, deckResponse, deckUpdate, deckCreate, CardResponse, CardUpdate, CardCreate


class DatabaseAPI(ABC):

    @classmethod
    @abstractmethod
    def start_db(cls):
        ...

    # --- topic ---
    @abstractmethod
    def list_topics(self) -> list[topicResponse]:
        ...

    @abstractmethod
    def get_topic(self, topic_id: int) -> topicResponse | None:
        ...

    @abstractmethod
    def create_topics(self, create_topic: topicCreate) -> topicResponse:
        ...

    @abstractmethod
    def update_topics(self, update_topic: topicUpdate) -> topicResponse | None:
        ...

    @abstractmethod
    def delete_topic(self, topic_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        ...


    # --- Decks ---

    @abstractmethod
    def list_decks(self) -> list[deckResponse]:
        ...

    @abstractmethod
    def list_decks_by_topic(self, topic_id) -> list[deckResponse] | None:
        """None if topic doesnt exist"""
        ...

    @abstractmethod
    def get_deck(self, deck_id: int) -> deckResponse | None:
        ...

    @abstractmethod
    def create_deck(self, create_deck: deckCreate) -> deckResponse | None:
        """None if topic doesnt exist"""
        ...

    @abstractmethod
    def update_deck(self, update_deck: deckUpdate) -> deckResponse | None:
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

