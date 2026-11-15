from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.routers.schemas import DeckCreate, DeckUpdate
from app.database.schemas import DeckResponse as DbDeckResponse, CardResponse as DbCardResponse, CardStats
import app.services.deck_service as svc


def _make_deck(id=1, name="Vocab", description=None, topic_id=None) -> DbDeckResponse:
    return DbDeckResponse(id=id, name=name, description=description, topic_id=topic_id)


def _make_card(
    id=1, deck_id=1, front="Q", back="A",
    front_image=None, back_image=None,
) -> DbCardResponse:
    return DbCardResponse(
        id=id, deck_id=deck_id, front=front, back=back,
        front_image=front_image, back_image=back_image,
        state=1, step=0, due=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.get_card_stats.return_value = CardStats()
    with patch("app.services.deck_service.db") as mock_db:
        mock_db.return_value.__enter__ = MagicMock(return_value=api)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        yield api


# ── stats ──────────────────────────────────────────────────────────────────────

class TestDeckStats:
    def test_maps_card_stats(self, mock_api):
        mock_api.get_deck.return_value = _make_deck(id=1)
        mock_api.get_card_stats.return_value = CardStats(
            total=10, due=4, new=3, learning=2, review=4, relearning=1
        )
        stats = svc.get_deck(1).stats
        assert stats.total_cards == 10
        assert stats.due_cards == 4
        assert stats.new_cards == 3
        assert stats.learning_cards == 2
        assert stats.review_cards == 4
        assert stats.relearning_cards == 1

    def test_asks_for_stats_of_that_deck_as_of_now(self, mock_api):
        mock_api.get_deck.return_value = _make_deck(id=7)
        before = datetime.now(timezone.utc)
        svc.get_deck(7)
        args, kwargs = mock_api.get_card_stats.call_args
        assert kwargs == {"deck_id": 7}
        assert before <= args[0] <= datetime.now(timezone.utc)


# ── list_decks ─────────────────────────────────────────────────────────────────

class TestListDecks:
    def test_returns_lean_list(self, mock_api):
        mock_api.list_decks.return_value = [
            _make_deck(id=1, name="A"),
            _make_deck(id=2, name="B"),
        ]
        result = svc.list_decks()
        assert len(result) == 2
        assert result[0].name == "A"

    def test_empty(self, mock_api):
        mock_api.list_decks.return_value = []
        assert svc.list_decks() == []


# ── list_decks_overview ────────────────────────────────────────────────────────

class TestListDecksOverview:
    def test_includes_stats(self, mock_api):
        mock_api.list_decks.return_value = [_make_deck(id=1, name="D")]
        mock_api.get_card_stats.return_value = CardStats(total=1, due=1, new=1)
        result = svc.list_decks_overview()
        assert len(result) == 1
        assert result[0].stats.total_cards == 1
        assert result[0].stats.due_cards == 1

    def test_stats_per_deck(self, mock_api):
        mock_api.list_decks.return_value = [_make_deck(id=1), _make_deck(id=2)]
        mock_api.get_card_stats.side_effect = lambda now, deck_id: CardStats(total=deck_id * 10)
        result = svc.list_decks_overview()
        assert [d.stats.total_cards for d in result] == [10, 20]

    def test_missing_stats_treated_as_empty(self, mock_api):
        mock_api.list_decks.return_value = [_make_deck(id=1)]
        mock_api.get_card_stats.return_value = None
        result = svc.list_decks_overview()
        assert result[0].stats.total_cards == 0

    def test_empty_deck_list(self, mock_api):
        mock_api.list_decks.return_value = []
        assert svc.list_decks_overview() == []


# ── get_deck ───────────────────────────────────────────────────────────────────

class TestGetDeck:
    def test_existing(self, mock_api):
        mock_api.get_deck.return_value = _make_deck(id=1, name="Science")
        result = svc.get_deck(1)
        assert result is not None
        assert result.name == "Science"

    def test_missing_returns_none(self, mock_api):
        mock_api.get_deck.return_value = None
        assert svc.get_deck(999) is None


# ── create_deck ────────────────────────────────────────────────────────────────

class TestCreateDeck:
    def test_standalone(self, mock_api):
        mock_api.create_deck.return_value = _make_deck(id=1, name="Standalone")
        result = svc.create_deck(DeckCreate(name="Standalone"))
        assert result is not None
        assert result.name == "Standalone"
        assert result.stats.total_cards == 0

    def test_with_topic(self, mock_api):
        mock_api.create_deck.return_value = _make_deck(id=2, name="Linked", topic_id=5)
        result = svc.create_deck(DeckCreate(name="Linked", topic_id=5))
        assert result.topic_id == 5

    def test_db_returns_none_propagates(self, mock_api):
        mock_api.create_deck.return_value = None
        result = svc.create_deck(DeckCreate(name="Bad", topic_id=999))
        assert result is None

    def test_passes_correct_data_to_db(self, mock_api):
        mock_api.create_deck.return_value = _make_deck(id=1, name="X")
        svc.create_deck(DeckCreate(name="X", description="desc"))
        call_arg = mock_api.create_deck.call_args[0][0]
        assert call_arg.name == "X"
        assert call_arg.description == "desc"


# ── update_deck ────────────────────────────────────────────────────────────────

class TestUpdateDeck:
    def test_existing(self, mock_api):
        mock_api.update_deck.return_value = _make_deck(id=1, name="Updated")
        result = svc.update_deck(1, DeckUpdate(name="Updated"))
        assert result is not None
        assert result.name == "Updated"

    def test_missing_returns_none(self, mock_api):
        mock_api.update_deck.return_value = None
        assert svc.update_deck(999, DeckUpdate(name="X")) is None

    def test_passes_id_to_db(self, mock_api):
        mock_api.update_deck.return_value = _make_deck(id=7, name="Y")
        svc.update_deck(7, DeckUpdate(name="Y"))
        call_arg = mock_api.update_deck.call_args[0][0]
        assert call_arg.id == 7


# ── delete_deck ────────────────────────────────────────────────────────────────

class TestDeleteDeck:
    def test_existing_returns_true(self, mock_api):
        mock_api.delete_deck.return_value = True
        assert svc.delete_deck(1) is True

    def test_missing_returns_false(self, mock_api):
        mock_api.delete_deck.return_value = False
        assert svc.delete_deck(999) is False

    def test_deletes_card_images(self, mock_api):
        mock_api.list_cards.return_value = [_make_card(id=1, front_image="f.png", back_image="b.png")]
        mock_api.delete_deck.return_value = True
        with patch("app.services.deck_service.delete_image") as delete_image:
            svc.delete_deck(1)
        assert {c.args[0] for c in delete_image.call_args_list} == {"f.png", "b.png"}


# ── list_deck_cards ────────────────────────────────────────────────────────────

class TestListDeckCards:
    def test_returns_card_list(self, mock_api):
        mock_api.list_cards.return_value = [
            _make_card(id=1), _make_card(id=2),
        ]
        result = svc.list_deck_cards(1)
        assert result is not None
        assert len(result) == 2

    def test_missing_deck_returns_none(self, mock_api):
        mock_api.list_cards.return_value = None
        assert svc.list_deck_cards(999) is None

    def test_empty_deck_returns_empty_list(self, mock_api):
        assert svc.list_deck_cards(1) == []


# ── reorder_deck_cards ─────────────────────────────────────────────────────────

class TestReorderDeckCards:
    def test_returns_reordered_cards(self, mock_api):
        mock_api.reorder_cards.return_value = [_make_card(id=2), _make_card(id=1)]
        result = svc.reorder_deck_cards(1, [2, 1])
        assert [c.id for c in result] == [2, 1]
        mock_api.reorder_cards.assert_called_once_with(1, [2, 1])

    def test_missing_deck_returns_none(self, mock_api):
        mock_api.reorder_cards.return_value = None
        assert svc.reorder_deck_cards(999, [1]) is None
