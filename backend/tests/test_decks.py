import pytest

from app.database.schemas import topicCreate, deckCreate, deckUpdate


class TestListDecks:
    def test_empty(self, api):
        assert api.list_decks() == []

    def test_returns_all(self, api):
        api.create_deck(deckCreate(name="A"))
        api.create_deck(deckCreate(name="B"))
        assert len(api.list_decks()) == 2


class TestListDecksByTopic:
    def test_returns_decks_for_topic(self, api):
        topic = api.create_topics(topicCreate(name="T"))
        api.create_deck(deckCreate(name="D1", topic_id=topic.id))
        api.create_deck(deckCreate(name="D2", topic_id=topic.id))
        api.create_deck(deckCreate(name="D3"))  # standalone, no topic
        result = api.list_decks_by_topic(topic.id)
        assert result is not None
        assert len(result) == 2
        assert all(d.topic_id == topic.id for d in result)

    def test_missing_topic_returns_none(self, api):
        assert api.list_decks_by_topic(999) is None

    def test_topic_with_no_decks_returns_empty_list(self, api):
        topic = api.create_topics(topicCreate(name="Empty"))
        result = api.list_decks_by_topic(topic.id)
        assert result == []


class TestGetDeck:
    def test_existing(self, api):
        created = api.create_deck(deckCreate(name="Vocab"))
        result = api.get_deck(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.name == "Vocab"

    def test_missing_returns_none(self, api):
        assert api.get_deck(999) is None


class TestCreateDeck:
    def test_standalone(self, api):
        result = api.create_deck(deckCreate(name="Standalone"))
        assert result.id is not None
        assert result.name == "Standalone"
        assert result.topic_id is None

    def test_with_topic(self, api):
        topic = api.create_topics(topicCreate(name="Topic"))
        result = api.create_deck(deckCreate(name="Linked", topic_id=topic.id))
        assert result.topic_id == topic.id

    def test_nonexistent_topic_returns_none(self, api):
        assert api.create_deck(deckCreate(name="Bad", topic_id=999)) is None

    def test_assigns_unique_ids(self, api):
        a = api.create_deck(deckCreate(name="A"))
        b = api.create_deck(deckCreate(name="B"))
        assert a.id != b.id


class TestUpdateDeck:
    def test_update_name(self, api):
        created = api.create_deck(deckCreate(name="Old"))
        result = api.update_deck(deckUpdate(id=created.id, name="New"))
        assert result is not None
        assert result.name == "New"

    def test_partial_update_preserves_fields(self, api):
        topic = api.create_topics(topicCreate(name="T"))
        created = api.create_deck(deckCreate(name="D", description="desc", topic_id=topic.id))
        result = api.update_deck(deckUpdate(id=created.id, name="D2"))
        assert result.description == "desc"
        assert result.topic_id == topic.id

    def test_missing_returns_none(self, api):
        assert api.update_deck(deckUpdate(id=999, name="X")) is None


class TestDeleteDeck:
    def test_deletes_existing(self, api):
        created = api.create_deck(deckCreate(name="Temp"))
        assert api.delete_deck(created.id) is True
        assert api.get_deck(created.id) is None

    def test_missing_returns_false(self, api):
        assert api.delete_deck(999) is False

    def test_cascade_deletes_cards(self, api):
        from app.database.schemas import CardCreate

        deck = api.create_deck(deckCreate(name="D"))
        card = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        api.delete_deck(deck.id)
        assert api.get_card(card.id) is None
