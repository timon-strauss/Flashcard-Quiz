from datetime import date

import pytest

from app.database.schemas import topicCreate, topicUpdate


class TestListTopics:
    def test_empty(self, api):
        assert api.list_topics() == []

    def test_returns_all(self, api):
        api.create_topics(topicCreate(name="A"))
        api.create_topics(topicCreate(name="B"))
        assert len(api.list_topics()) == 2


class TestGetTopic:
    def test_existing(self, api):
        created = api.create_topics(topicCreate(name="Math"))
        result = api.get_topic(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.name == "Math"

    def test_missing_returns_none(self, api):
        assert api.get_topic(999) is None


class TestCreateTopic:
    def test_minimal(self, api):
        result = api.create_topics(topicCreate(name="Physics"))
        assert result.id is not None
        assert result.name == "Physics"
        assert result.description is None
        assert result.exam_date is None

    def test_full(self, api):
        result = api.create_topics(
            topicCreate(name="Chemistry", description="Organic", exam_date=date(2026, 6, 1))
        )
        assert result.description == "Organic"
        assert result.exam_date == date(2026, 6, 1)

    def test_assigns_unique_ids(self, api):
        a = api.create_topics(topicCreate(name="A"))
        b = api.create_topics(topicCreate(name="B"))
        assert a.id != b.id


class TestUpdateTopic:
    def test_update_name(self, api):
        created = api.create_topics(topicCreate(name="Old"))
        result = api.update_topics(topicUpdate(id=created.id, name="New"))
        assert result is not None
        assert result.name == "New"

    def test_partial_update_preserves_fields(self, api):
        created = api.create_topics(
            topicCreate(name="Bio", description="Life science", exam_date=date(2026, 5, 10))
        )
        result = api.update_topics(topicUpdate(id=created.id, name="Biology"))
        assert result.description == "Life science"
        assert result.exam_date == date(2026, 5, 10)

    def test_missing_returns_none(self, api):
        assert api.update_topics(topicUpdate(id=999, name="X")) is None


class TestDeleteTopic:
    def test_deletes_existing(self, api):
        created = api.create_topics(topicCreate(name="Temp"))
        assert api.delete_topic(created.id) is True
        assert api.get_topic(created.id) is None

    def test_missing_returns_false(self, api):
        assert api.delete_topic(999) is False

    def test_cascade_deletes_decks(self, api):
        from app.database.schemas import deckCreate

        topic = api.create_topics(topicCreate(name="Topic"))
        deck = api.create_deck(deckCreate(name="Deck", topic_id=topic.id))
        api.delete_topic(topic.id)
        assert api.get_deck(deck.id) is None
