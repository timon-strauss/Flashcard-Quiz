from datetime import datetime

import pytest

from app.database.schemas import topicCreate, deckCreate, CardCreate, CardUpdate


@pytest.fixture
def deck(api):
    return api.create_deck(deckCreate(name="Default Deck"))


class TestListCards:
    def test_empty(self, api):
        assert api.list_cards() == []

    def test_returns_all(self, api, deck):
        api.create_card(CardCreate(front="Q1", back="A1", deck_id=deck.id))
        api.create_card(CardCreate(front="Q2", back="A2", deck_id=deck.id))
        assert len(api.list_cards()) == 2


class TestListCardsByDeck:
    def test_returns_cards_for_deck(self, api, deck):
        deck2 = api.create_deck(deckCreate(name="Other Deck"))
        api.create_card(CardCreate(front="Q1", back="A1", deck_id=deck.id))
        api.create_card(CardCreate(front="Q2", back="A2", deck_id=deck.id))
        api.create_card(CardCreate(front="Q3", back="A3", deck_id=deck2.id))
        result = api.list_cards_by_deck(deck.id)
        assert result is not None
        assert len(result) == 2
        assert all(c.deck_id == deck.id for c in result)

    def test_missing_deck_returns_none(self, api):
        assert api.list_cards_by_deck(999) is None

    def test_deck_with_no_cards_returns_empty_list(self, api, deck):
        assert api.list_cards_by_deck(deck.id) == []


class TestListCardsByTopic:
    def test_returns_cards_across_decks_in_topic(self, api):
        topic = api.create_topics(topicCreate(name="T"))
        d1 = api.create_deck(deckCreate(name="D1", topic_id=topic.id))
        d2 = api.create_deck(deckCreate(name="D2", topic_id=topic.id))
        api.create_card(CardCreate(front="Q1", back="A1", deck_id=d1.id))
        api.create_card(CardCreate(front="Q2", back="A2", deck_id=d2.id))
        result = api.list_cards_by_topic(topic.id)
        assert result is not None
        assert len(result) == 2

    def test_excludes_standalone_deck_cards(self, api):
        topic = api.create_topics(topicCreate(name="T"))
        topic_deck = api.create_deck(deckCreate(name="Linked", topic_id=topic.id))
        standalone = api.create_deck(deckCreate(name="Standalone"))
        api.create_card(CardCreate(front="Q1", back="A1", deck_id=topic_deck.id))
        api.create_card(CardCreate(front="Q2", back="A2", deck_id=standalone.id))
        result = api.list_cards_by_topic(topic.id)
        assert len(result) == 1

    def test_missing_topic_returns_none(self, api):
        assert api.list_cards_by_topic(999) is None

    def test_topic_with_no_cards_returns_empty_list(self, api):
        topic = api.create_topics(topicCreate(name="Empty"))
        api.create_deck(deckCreate(name="D", topic_id=topic.id))
        assert api.list_cards_by_topic(topic.id) == []


class TestGetCard:
    def test_existing(self, api, deck):
        created = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        result = api.get_card(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.front == "Q"
        assert result.back == "A"

    def test_missing_returns_none(self, api):
        assert api.get_card(999) is None


class TestCreateCard:
    def test_minimal(self, api, deck):
        result = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        assert result.id is not None
        assert result.front == "Q"
        assert result.back == "A"
        assert result.deck_id == deck.id
        assert result.memorized is False
        assert result.last_seen_at is None

    def test_with_images(self, api, deck):
        result = api.create_card(
            CardCreate(front="Q", back="A", deck_id=deck.id, front_image="f.png", back_image="b.png")
        )
        assert result.front_image == "f.png"
        assert result.back_image == "b.png"

    def test_nonexistent_deck_returns_none(self, api):
        assert api.create_card(CardCreate(front="Q", back="A", deck_id=999)) is None

    def test_assigns_unique_ids(self, api, deck):
        a = api.create_card(CardCreate(front="Q1", back="A1", deck_id=deck.id))
        b = api.create_card(CardCreate(front="Q2", back="A2", deck_id=deck.id))
        assert a.id != b.id


class TestUpdateCard:
    def test_update_front(self, api, deck):
        created = api.create_card(CardCreate(front="Old", back="A", deck_id=deck.id))
        result = api.update_card(CardUpdate(id=created.id, front="New"))
        assert result is not None
        assert result.front == "New"

    def test_update_memorized(self, api, deck):
        created = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        result = api.update_card(CardUpdate(id=created.id, memorized=True))
        assert result.memorized is True

    def test_update_last_seen_at(self, api, deck):
        created = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        ts = datetime(2026, 1, 15, 12, 0, 0)
        result = api.update_card(CardUpdate(id=created.id, last_seen_at=ts))
        assert result.last_seen_at == ts

    def test_partial_update_preserves_fields(self, api, deck):
        created = api.create_card(
            CardCreate(front="Q", back="A", deck_id=deck.id, front_image="f.png")
        )
        result = api.update_card(CardUpdate(id=created.id, back="Updated"))
        assert result.front == "Q"
        assert result.front_image == "f.png"
        assert result.deck_id == deck.id

    def test_missing_returns_none(self, api):
        assert api.update_card(CardUpdate(id=999)) is None


class TestDeleteCard:
    def test_deletes_existing(self, api, deck):
        created = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        assert api.delete_card(created.id) is True
        assert api.get_card(created.id) is None

    def test_missing_returns_false(self, api):
        assert api.delete_card(999) is False
