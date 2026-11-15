from abc import ABC, abstractmethod
from datetime import datetime

from .schemas import (
    TopicResponse, TopicUpdate, TopicCreate,
    DeckResponse, DeckUpdate, DeckCreate,
    CardResponse, CardUpdate, CardCreate,
    CardReview, ReviewLogResponse, CardStats,
)


class DatabaseAPI(ABC):
    """Storage interface. All datetimes going in and out are timezone-aware (UTC)."""

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
    def create_topic(self, create_topic: TopicCreate) -> TopicResponse:
        ...

    @abstractmethod
    def update_topic(self, update_topic: TopicUpdate) -> TopicResponse | None:
        ...

    @abstractmethod
    def delete_topic(self, topic_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        ...

    # --- Decks ---

    @abstractmethod
    def list_decks(
        self, topic_id: int | None = None, without_topic: bool = False
    ) -> list[DeckResponse] | None:
        """All decks by default, the decks of a topic with topic_id,
        or only the decks that belong to no topic with without_topic.

        None if topic doesnt exist
        """
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
    def list_cards(
        self, deck_id: int | None = None, topic_id: int | None = None
    ) -> list[CardResponse] | None:
        """All cards by default, or those of one deck / topic, ordered by position.

        None if deck / topic doesnt exist
        """
        ...

    @abstractmethod
    def get_card(self, card_id: int) -> CardResponse | None:
        ...

    @abstractmethod
    def create_card(self, create_card: CardCreate) -> CardResponse | None:
        """New cards are in Learning and due immediately. None if deck doesnt exist"""
        ...

    @abstractmethod
    def update_card(self, update_card: CardUpdate) -> CardResponse | None:
        """Changes content only, never the scheduling state."""
        ...

    @abstractmethod
    def delete_card(self, card_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    def reorder_cards(self, deck_id: int, card_ids: list[int]) -> list[CardResponse] | None:
        """Sets the positions to the order of card_ids. None if deck doesnt exist"""
        ...

    # --- Reviews / FSRS ---

    @abstractmethod
    def review_card(self, review: CardReview) -> CardResponse | None:
        """Stores the new scheduling state and the review log in one transaction.

        None if card doesnt exist
        """
        ...

    @abstractmethod
    def list_due_cards(
        self,
        due_before: datetime,
        deck_id: int | None = None,
        topic_id: int | None = None,
        limit: int | None = None,
    ) -> list[CardResponse] | None:
        """Cards with due <= due_before, most overdue first. None if deck / topic doesnt exist"""
        ...

    @abstractmethod
    def list_review_logs(
        self,
        card_id: int | None = None,
        deck_id: int | None = None,
        topic_id: int | None = None,
        since: datetime | None = None,
    ) -> list[ReviewLogResponse] | None:
        """Oldest first. None if card / deck / topic doesnt exist"""
        ...

    @abstractmethod
    def get_card_stats(
        self,
        due_before: datetime,
        deck_id: int | None = None,
        topic_id: int | None = None,
    ) -> CardStats | None:
        """Card counts per state, how many are due (due <= due_before), how many are ready
        for the exam of their topic as of `due_before`, and the most recent review.

        Over all cards by default. None if deck / topic doesnt exist
        """
        ...


from .SQLlite import SQLite

db: type[DatabaseAPI] = SQLite
