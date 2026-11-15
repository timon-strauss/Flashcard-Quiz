from app.database.schemas import TopicCreate, DeckCreate, DeckUpdate, CardCreate


class TestListDecks:
    def test_empty(self, api):
        assert api.list_decks() == []

    def test_returns_all(self, api):
        topic = api.create_topic(TopicCreate(name="T"))
        api.create_deck(DeckCreate(name="A", topic_id=topic.id))
        api.create_deck(DeckCreate(name="B"))
        assert len(api.list_decks()) == 2

    def test_filter_by_topic(self, api):
        topic = api.create_topic(TopicCreate(name="T"))
        api.create_deck(DeckCreate(name="D1", topic_id=topic.id))
        api.create_deck(DeckCreate(name="D2", topic_id=topic.id))
        api.create_deck(DeckCreate(name="D3"))  # standalone, no topic
        result = api.list_decks(topic_id=topic.id)
        assert result is not None
        assert len(result) == 2
        assert all(d.topic_id == topic.id for d in result)

    def test_missing_topic_returns_none(self, api):
        assert api.list_decks(topic_id=999) is None

    def test_topic_with_no_decks_returns_empty_list(self, api):
        topic = api.create_topic(TopicCreate(name="Empty"))
        assert api.list_decks(topic_id=topic.id) == []

    def test_without_topic_returns_only_standalone_decks(self, api):
        topic = api.create_topic(TopicCreate(name="T"))
        api.create_deck(DeckCreate(name="Linked", topic_id=topic.id))
        standalone = api.create_deck(DeckCreate(name="Standalone"))
        result = api.list_decks(without_topic=True)
        assert [d.id for d in result] == [standalone.id]


class TestGetDeck:
    def test_existing(self, api):
        created = api.create_deck(DeckCreate(name="Vocab"))
        result = api.get_deck(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.name == "Vocab"

    def test_missing_returns_none(self, api):
        assert api.get_deck(999) is None


class TestCreateDeck:
    def test_standalone(self, api):
        result = api.create_deck(DeckCreate(name="Standalone"))
        assert result.id is not None
        assert result.name == "Standalone"
        assert result.topic_id is None

    def test_with_topic(self, api):
        topic = api.create_topic(TopicCreate(name="Topic"))
        result = api.create_deck(DeckCreate(name="Linked", topic_id=topic.id))
        assert result.topic_id == topic.id

    def test_nonexistent_topic_returns_none(self, api):
        assert api.create_deck(DeckCreate(name="Bad", topic_id=999)) is None

    def test_assigns_unique_ids(self, api):
        a = api.create_deck(DeckCreate(name="A"))
        b = api.create_deck(DeckCreate(name="B"))
        assert a.id != b.id


class TestUpdateDeck:
    def test_update_name(self, api):
        created = api.create_deck(DeckCreate(name="Old"))
        result = api.update_deck(DeckUpdate(id=created.id, name="New"))
        assert result is not None
        assert result.name == "New"

    def test_partial_update_preserves_fields(self, api):
        topic = api.create_topic(TopicCreate(name="T"))
        created = api.create_deck(DeckCreate(name="D", description="desc", topic_id=topic.id))
        result = api.update_deck(DeckUpdate(id=created.id, name="D2"))
        assert result.description == "desc"
        assert result.topic_id == topic.id

    def test_move_to_topic_and_back(self, api):
        topic = api.create_topic(TopicCreate(name="T"))
        created = api.create_deck(DeckCreate(name="D"))
        moved = api.update_deck(DeckUpdate(id=created.id, topic_id=topic.id))
        assert moved.topic_id == topic.id
        removed = api.update_deck(DeckUpdate(id=created.id, topic_id=None))
        assert removed.topic_id is None

    def test_missing_returns_none(self, api):
        assert api.update_deck(DeckUpdate(id=999, name="X")) is None


class TestDeleteDeck:
    def test_deletes_existing(self, api):
        created = api.create_deck(DeckCreate(name="Temp"))
        assert api.delete_deck(created.id) is True
        assert api.get_deck(created.id) is None

    def test_missing_returns_false(self, api):
        assert api.delete_deck(999) is False

    def test_cascade_deletes_cards(self, api):
        deck = api.create_deck(DeckCreate(name="D"))
        card = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
        api.delete_deck(deck.id)
        assert api.get_card(card.id) is None
