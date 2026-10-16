from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
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
    memorized = Column(Boolean, nullable=False, default=False)
    last_seen_at = Column(DateTime, nullable=True)

    deck = relationship("Deck", back_populates="cards")
