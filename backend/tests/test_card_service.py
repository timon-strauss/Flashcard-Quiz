from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest

from app.routers.schemas import CardCreate, CardUpdate, CardMemorizedUpdate
from app.database.schemas import CardResponse as DbCardResponse
import app.services.card_service as svc


def _make_card(
    id=1, deck_id=1, front="Q", back="A",
    front_image=None, back_image=None,
    memorized=False, last_seen_at=None,
) -> DbCardResponse:
    return DbCardResponse(
        id=id, deck_id=deck_id, front=front, back=back,
        front_image=front_image, back_image=back_image,
        memorized=memorized, last_seen_at=last_seen_at,
    )


@pytest.fixture
def mock_api():
    api = MagicMock()
    with patch("app.services.card_service.db") as mock_db:
        mock_db.return_value.__enter__ = MagicMock(return_value=api)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        yield api


# ── get_card ───────────────────────────────────────────────────────────────────

class TestGetCard:
    def test_existing(self, mock_api):
        mock_api.get_card.return_value = _make_card(id=1, front="Hello", back="World")
        result = svc.get_card(1)
        assert result is not None
        assert result.id == 1
        assert result.front == "Hello"
        assert result.back == "World"

    def test_missing_returns_none(self, mock_api):
        mock_api.get_card.return_value = None
        assert svc.get_card(999) is None


# ── create_card ────────────────────────────────────────────────────────────────

class TestCreateCard:
    def test_minimal(self, mock_api):
        mock_api.create_card.return_value = _make_card(id=1)
        result = svc.create_card(CardCreate(deck_id=1, front="Q", back="A"))
        assert result is not None
        assert result.id == 1
        assert result.memorized is False
        assert result.last_seen_at is None

    def test_with_images(self, mock_api):
        mock_api.create_card.return_value = _make_card(
            id=2, front_image="f.png", back_image="b.png"
        )
        result = svc.create_card(
            CardCreate(deck_id=1, front="Q", back="A", front_image="f.png", back_image="b.png")
        )
        assert result.front_image == "f.png"
        assert result.back_image == "b.png"

    def test_db_returns_none_propagates(self, mock_api):
        mock_api.create_card.return_value = None
        result = svc.create_card(CardCreate(deck_id=999, front="Q", back="A"))
        assert result is None

    def test_passes_correct_data_to_db(self, mock_api):
        mock_api.create_card.return_value = _make_card(id=1)
        svc.create_card(CardCreate(deck_id=3, front="Front", back="Back"))
        call_arg = mock_api.create_card.call_args[0][0]
        assert call_arg.deck_id == 3
        assert call_arg.front == "Front"
        assert call_arg.back == "Back"


# ── update_card ────────────────────────────────────────────────────────────────

class TestUpdateCard:
    def test_existing(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=1, front="Updated")
        result = svc.update_card(1, CardUpdate(front="Updated"))
        assert result is not None
        assert result.front == "Updated"

    def test_missing_returns_none(self, mock_api):
        mock_api.update_card.return_value = None
        assert svc.update_card(999, CardUpdate(front="X")) is None

    def test_passes_id_to_db(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=4)
        svc.update_card(4, CardUpdate(back="New"))
        call_arg = mock_api.update_card.call_args[0][0]
        assert call_arg.id == 4

    def test_only_set_fields_forwarded(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=1)
        svc.update_card(1, CardUpdate(front="New"))
        call_arg = mock_api.update_card.call_args[0][0]
        dumped = call_arg.model_dump(exclude_unset=True)
        assert "front" in dumped
        assert "back" not in dumped


# ── delete_card ────────────────────────────────────────────────────────────────

class TestDeleteCard:
    def test_existing_returns_true(self, mock_api):
        mock_api.delete_card.return_value = True
        assert svc.delete_card(1) is True

    def test_missing_returns_false(self, mock_api):
        mock_api.delete_card.return_value = False
        assert svc.delete_card(999) is False


# ── mark_card_seen ─────────────────────────────────────────────────────────────

class TestMarkCardSeen:
    def test_updates_last_seen_at(self, mock_api):
        ts = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_api.update_card.return_value = _make_card(id=1, last_seen_at=ts)
        result = svc.mark_card_seen(1)
        assert result is not None
        assert result.last_seen_at == ts

    def test_missing_returns_none(self, mock_api):
        mock_api.update_card.return_value = None
        assert svc.mark_card_seen(999) is None

    def test_passes_id_and_timestamp_to_db(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=2)
        svc.mark_card_seen(2)
        call_arg = mock_api.update_card.call_args[0][0]
        assert call_arg.id == 2
        assert call_arg.last_seen_at is not None

    def test_timestamp_is_utc(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=1)
        svc.mark_card_seen(1)
        call_arg = mock_api.update_card.call_args[0][0]
        assert call_arg.last_seen_at.tzinfo == timezone.utc


# ── set_card_memorized ─────────────────────────────────────────────────────────

class TestSetCardMemorized:
    def test_mark_memorized(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=1, memorized=True)
        result = svc.set_card_memorized(1, CardMemorizedUpdate(memorized=True))
        assert result is not None
        assert result.memorized is True

    def test_unmark_memorized(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=1, memorized=False)
        result = svc.set_card_memorized(1, CardMemorizedUpdate(memorized=False))
        assert result.memorized is False

    def test_missing_returns_none(self, mock_api):
        mock_api.update_card.return_value = None
        assert svc.set_card_memorized(999, CardMemorizedUpdate(memorized=True)) is None

    def test_passes_correct_memorized_flag_to_db(self, mock_api):
        mock_api.update_card.return_value = _make_card(id=3)
        svc.set_card_memorized(3, CardMemorizedUpdate(memorized=True))
        call_arg = mock_api.update_card.call_args[0][0]
        assert call_arg.id == 3
        assert call_arg.memorized is True
