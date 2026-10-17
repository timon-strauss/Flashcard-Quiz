from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.routers.schemas import DeckCreate, DeckUpdate
from app.database.schemas import DeckResponse as DbDeckResponse, CardResponse as DbCardResponse
import app.services.deck_service as svc


def _make_deck(id=1, name="Vocab", description=None, topic_id=None) -> DbDeckResponse:
    return DbDeckResponse(id=id, name=name, description=description, topic_id=topic_id)


def _make_card(id=1, deck_id=1, memorized=False, last_seen_at=None) -> DbCardResponse:
    return DbCardResponse(
        id=id, deck_id=deck_id, front="Q", back="A",
        memorized=memorized, last_seen_at=last_seen_at,
    )


@pytest.fixture
def mock_api():
    api = MagicMock()
    with patch("app.services.deck_service.db") as mock_db:
        mock_db.return_value.__enter__ = MagicMock(return_value=api)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        yield api


# ── _compute_deck_stats ────────────────────────────────────────────────────────

class TestComputeDeckStats:
    def test_empty_deck(self):
        stats = svc._compute_deck_stats([])
        assert stats.total_cards == 0
        assert stats.memorized_cards == 0
        assert stats.avg_days_since_seen is None

    def test_counts_memorized(self):
        cards = [_make_card(id=1, memorized=True), _make_card(id=2, memorized=False)]
        stats = svc._compute_deck_stats(cards)
        assert stats.total_cards == 2
        assert stats.memorized_cards == 1

    def test_avg_days_since_seen(self):
        today = date.today()
        from datetime import timedelta
        ts = datetime.combine(today - timedelta(days=3), datetime.min.time())
        cards = [_make_card(id=1, last_seen_at=ts)]
        stats = svc._compute_deck_stats(cards)
        assert stats.avg_days_since_seen == 3.0

    def test_avg_ignores_none_last_seen(self):
        today = date.today()
        from datetime import timedelta
        ts = datetime.combine(today - timedelta(days=6), datetime.min.time())
        cards = [_make_card(id=1, last_seen_at=ts), _make_card(id=2, last_seen_at=None)]
        stats = svc._compute_deck_stats(cards)
        assert stats.avg_days_since_seen == 6.0

    def test_all_unseen_returns_none_avg(self):
        cards = [_make_card(id=1), _make_card(id=2)]
        stats = svc._compute_deck_stats(cards)
        assert stats.avg_days_since_seen is None


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
        deck = _make_deck(id=1, name="D")
        mock_api.list_decks.return_value = [deck]
        mock_api.list_cards_by_deck.return_value = [_make_card(memorized=True)]
        result = svc.list_decks_overview()
        assert len(result) == 1
        assert result[0].stats.total_cards == 1
        assert result[0].stats.memorized_cards == 1

    def test_none_cards_treated_as_empty(self, mock_api):
        deck = _make_deck(id=1)
        mock_api.list_decks.return_value = [deck]
        mock_api.list_cards_by_deck.return_value = None
        result = svc.list_decks_overview()
        assert result[0].stats.total_cards == 0

    def test_empty_deck_list(self, mock_api):
        mock_api.list_decks.return_value = []
        assert svc.list_decks_overview() == []


# ── get_deck ───────────────────────────────────────────────────────────────────

class TestGetDeck:
    def test_existing(self, mock_api):
        mock_api.get_deck.return_value = _make_deck(id=1, name="Science")
        mock_api.list_cards_by_deck.return_value = []
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
        mock_api.list_cards_by_deck.return_value = []
        result = svc.create_deck(DeckCreate(name="Standalone"))
        assert result is not None
        assert result.name == "Standalone"
        assert result.stats.total_cards == 0

    def test_with_topic(self, mock_api):
        mock_api.create_deck.return_value = _make_deck(id=2, name="Linked", topic_id=5)
        mock_api.list_cards_by_deck.return_value = []
        result = svc.create_deck(DeckCreate(name="Linked", topic_id=5))
        assert result.topic_id == 5

    def test_db_returns_none_propagates(self, mock_api):
        mock_api.create_deck.return_value = None
        result = svc.create_deck(DeckCreate(name="Bad", topic_id=999))
        assert result is None

    def test_passes_correct_data_to_db(self, mock_api):
        mock_api.create_deck.return_value = _make_deck(id=1, name="X")
        mock_api.list_cards_by_deck.return_value = []
        svc.create_deck(DeckCreate(name="X", description="desc"))
        call_arg = mock_api.create_deck.call_args[0][0]
        assert call_arg.name == "X"
        assert call_arg.description == "desc"


# ── update_deck ────────────────────────────────────────────────────────────────

class TestUpdateDeck:
    def test_existing(self, mock_api):
        mock_api.update_deck.return_value = _make_deck(id=1, name="Updated")
        mock_api.list_cards_by_deck.return_value = []
        result = svc.update_deck(1, DeckUpdate(name="Updated"))
        assert result is not None
        assert result.name == "Updated"

    def test_missing_returns_none(self, mock_api):
        mock_api.update_deck.return_value = None
        assert svc.update_deck(999, DeckUpdate(name="X")) is None

    def test_passes_id_to_db(self, mock_api):
        mock_api.update_deck.return_value = _make_deck(id=7, name="Y")
        mock_api.list_cards_by_deck.return_value = []
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


# ── list_deck_cards ────────────────────────────────────────────────────────────

class TestListDeckCards:
    def test_returns_card_list(self, mock_api):
        mock_api.list_cards_by_deck.return_value = [
            _make_card(id=1), _make_card(id=2),
        ]
        result = svc.list_deck_cards(1)
        assert result is not None
        assert len(result) == 2

    def test_missing_deck_returns_none(self, mock_api):
        mock_api.list_cards_by_deck.return_value = None
        assert svc.list_deck_cards(999) is None

    def test_empty_deck_returns_empty_list(self, mock_api):
        mock_api.list_cards_by_deck.return_value = []
        assert svc.list_deck_cards(1) == []
