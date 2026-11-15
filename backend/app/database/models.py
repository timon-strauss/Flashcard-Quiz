from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    exam_date = Column(DateTime, nullable=True)

    decks = relationship("Deck", back_populates="topic", cascade="all, delete")


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    topic = relationship("Topic", back_populates="decks")
    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    front = Column(String, nullable=False)
    front_image = Column(String, nullable=True)
    back = Column(String, nullable=False)
    back_image = Column(String, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    # FSRS scheduling state
    # state: 1 = Learning, 2 = Review, 3 = Relearning (new card = Learning without last_review)
    state = Column(Integer, nullable=False, default=1)
    # index of the current (re)learning step; None once the card is in Review
    step = Column(Integer, nullable=True, default=0)
    # None until the first review
    stability = Column(Float, nullable=True)
    difficulty = Column(Float, nullable=True)
    due = Column(DateTime, nullable=False, index=True)
    last_review = Column(DateTime, nullable=True)

    deck = relationship("Deck", back_populates="cards")
    review_logs = relationship(
        "ReviewLog", back_populates="card", cascade="all, delete-orphan"
    )


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, index=True)
    # rating: 1 = Again, 2 = Hard, 3 = Good, 4 = Easy
    rating = Column(Integer, nullable=False)
    reviewed_at = Column(DateTime, nullable=False)

    card = relationship("Card", back_populates="review_logs")
