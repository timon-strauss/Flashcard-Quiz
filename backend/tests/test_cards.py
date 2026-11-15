from datetime import datetime, timedelta, timezone

import pytest

from app.database.schemas import DeckCreate, CardCreate, CardUpdate, CardReview


@pytest.fixture
def deck(api):
    return api.create_deck(DeckCreate(name="Default Deck"))


def _card(api, deck, front="Q", back="A"):
    return api.create_card(CardCreate(front=front, back=back, deck_id=deck.id))


class TestListCards:
    def test_empty(self, api):
        assert api.list_cards() == []

    def test_returns_all(self, api, deck):
        deck2 = api.create_deck(DeckCreate(name="Other Deck"))
        _card(api, deck)
        _card(api, deck2)
        assert len(api.list_cards()) == 2

    def test_filter_by_deck(self, api, deck):
        deck2 = api.create_deck(DeckCreate(name="Other Deck"))
        _card(api, deck, "Q1")
        _card(api, deck, "Q2")
        _card(api, deck2, "Q3")
        result = api.list_cards(deck_id=deck.id)
        assert result is not None
        assert len(result) == 2
        assert all(c.deck_id == deck.id for c in result)

    def test_missing_deck_returns_none(self, api):
        assert api.list_cards(deck_id=999) is None

    def test_deck_with_no_cards_returns_empty_list(self, api, deck):
        assert api.list_cards(deck_id=deck.id) == []

    def test_ordered_by_position(self, api, deck):
        a = _card(api, deck, "Q1")
        b = _card(api, deck, "Q2")
        c = _card(api, deck, "Q3")
        api.reorder_cards(deck.id, [c.id, a.id, b.id])
        assert [x.id for x in api.list_cards(deck_id=deck.id)] == [c.id, a.id, b.id]


class TestGetCard:
    def test_existing(self, api, deck):
        created = _card(api, deck)
        result = api.get_card(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.front == "Q"
        assert result.back == "A"

    def test_missing_returns_none(self, api):
        assert api.get_card(999) is None


class TestCreateCard:
    def test_minimal(self, api, deck):
        result = _card(api, deck)
        assert result.id is not None
        assert result.front == "Q"
        assert result.back == "A"
        assert result.deck_id == deck.id
        assert result.front_image is None
        assert result.back_image is None

    def test_with_images(self, api, deck):
        result = api.create_card(
            CardCreate(front="Q", back="A", deck_id=deck.id, front_image="f.png", back_image="b.png")
        )
        assert result.front_image == "f.png"
        assert result.back_image == "b.png"

    def test_nonexistent_deck_returns_none(self, api):
        assert api.create_card(CardCreate(front="Q", back="A", deck_id=999)) is None

    def test_assigns_unique_ids(self, api, deck):
        assert _card(api, deck).id != _card(api, deck).id

    def test_position_counts_up_per_deck(self, api, deck):
        deck2 = api.create_deck(DeckCreate(name="Other Deck"))
        assert _card(api, deck).position == 0
        assert _card(api, deck).position == 1
        assert _card(api, deck2).position == 0

    def test_starts_as_new_fsrs_card(self, api, deck):
        result = _card(api, deck)
        assert result.state == 1  # Learning
        assert result.step == 0
        assert result.stability is None
        assert result.difficulty is None
        assert result.last_review is None

    def test_is_due_immediately_in_utc(self, api, deck):
        before = datetime.now(timezone.utc)
        result = _card(api, deck)
        after = datetime.now(timezone.utc)
        assert result.due.tzinfo == timezone.utc
        assert before <= result.due <= after


class TestUpdateCard:
    def test_update_front(self, api, deck):
        created = _card(api, deck, front="Old")
        result = api.update_card(CardUpdate(id=created.id, front="New"))
        assert result is not None
        assert result.front == "New"

    def test_partial_update_preserves_fields(self, api, deck):
        created = api.create_card(
            CardCreate(front="Q", back="A", deck_id=deck.id, front_image="f.png")
        )
        result = api.update_card(CardUpdate(id=created.id, back="Updated"))
        assert result.front == "Q"
        assert result.front_image == "f.png"
        assert result.deck_id == deck.id

    def test_remove_image(self, api, deck):
        created = api.create_card(
            CardCreate(front="Q", back="A", deck_id=deck.id, front_image="f.png")
        )
        result = api.update_card(CardUpdate(id=created.id, front_image=None))
        assert result.front_image is None

    def test_move_to_other_deck(self, api, deck):
        deck2 = api.create_deck(DeckCreate(name="Other Deck"))
        created = _card(api, deck)
        result = api.update_card(CardUpdate(id=created.id, deck_id=deck2.id))
        assert result.deck_id == deck2.id
        assert api.list_cards(deck_id=deck.id) == []

    def test_keeps_scheduling_state(self, api, deck):
        created = _card(api, deck)
        now = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        reviewed = api.review_card(CardReview(
            card_id=created.id, rating=3, reviewed_at=now,
            state=2, step=None, stability=3.5, difficulty=5.0, due=now + timedelta(days=3),
        ))
        result = api.update_card(CardUpdate(id=created.id, front="Changed"))
        for field in ("state", "step", "stability", "difficulty", "due", "last_review"):
            assert getattr(result, field) == getattr(reviewed, field)

    def test_scheduling_fields_are_not_updatable(self):
        assert not {"state", "step", "stability", "difficulty", "due", "last_review"} & set(
            CardUpdate.model_fields
        )

    def test_missing_returns_none(self, api):
        assert api.update_card(CardUpdate(id=999)) is None


class TestDeleteCard:
    def test_deletes_existing(self, api, deck):
        created = _card(api, deck)
        assert api.delete_card(created.id) is True
        assert api.get_card(created.id) is None

    def test_missing_returns_false(self, api):
        assert api.delete_card(999) is False


class TestReorderCards:
    def test_sets_positions_in_given_order(self, api, deck):
        a = _card(api, deck, "Q1")
        b = _card(api, deck, "Q2")
        c = _card(api, deck, "Q3")
        result = api.reorder_cards(deck.id, [b.id, c.id, a.id])
        assert [x.id for x in result] == [b.id, c.id, a.id]
        assert [x.position for x in result] == [0, 1, 2]

    def test_missing_deck_returns_none(self, api):
        assert api.reorder_cards(999, [1, 2]) is None

    def test_ignores_cards_of_other_decks_and_unknown_ids(self, api, deck):
        deck2 = api.create_deck(DeckCreate(name="Other Deck"))
        a = _card(api, deck, "Q1")
        b = _card(api, deck, "Q2")
        foreign = _card(api, deck2, "Q3")
        result = api.reorder_cards(deck.id, [foreign.id, 999, b.id, a.id])
        assert [x.id for x in result] == [b.id, a.id]
        assert api.get_card(foreign.id).position == 0
