from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.routers.schemas import TopicCreate, TopicUpdate
from app.database.schemas import TopicResponse as DbTopicResponse, CardResponse as DbCardResponse
import app.services.topic_service as svc


TODAY = date(2026, 6, 15)


def _make_topic(id=1, name="Math", description=None, exam_date=None) -> DbTopicResponse:
    return DbTopicResponse(id=id, name=name, description=description, exam_date=exam_date)


def _make_card(id=1, deck_id=1, memorized=False, last_seen_at=None) -> DbCardResponse:
    return DbCardResponse(
        id=id, deck_id=deck_id, front="Q", back="A",
        memorized=memorized, last_seen_at=last_seen_at,
    )


@pytest.fixture
def mock_api():
    api = MagicMock()
    with patch("app.services.topic_service.db") as mock_db:
        mock_db.return_value.__enter__ = MagicMock(return_value=api)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        yield api


# ── _compute_topic_stats ───────────────────────────────────────────────────────

class TestComputeTopicStats:
    def test_empty_deck(self):
        topic = _make_topic()
        stats = svc._compute_topic_stats(topic, [], TODAY)
        assert stats.total_cards == 0
        assert stats.memorized_cards == 0
        assert stats.avg_days_since_seen is None
        assert stats.days_until_exam is None

    def test_memorized_count(self):
        topic = _make_topic()
        cards = [_make_card(id=1, memorized=True), _make_card(id=2, memorized=False)]
        stats = svc._compute_topic_stats(topic, cards, TODAY)
        assert stats.total_cards == 2
        assert stats.memorized_cards == 1

    def test_avg_days_since_seen(self):
        topic = _make_topic()
        ts = datetime(2026, 6, 10, 0, 0, 0)  # 5 days before TODAY
        cards = [_make_card(id=1, last_seen_at=ts)]
        stats = svc._compute_topic_stats(topic, cards, TODAY)
        assert stats.avg_days_since_seen == 5.0

    def test_avg_ignores_unseen_cards(self):
        topic = _make_topic()
        ts = datetime(2026, 6, 5, 0, 0, 0)  # 10 days before TODAY
        cards = [_make_card(id=1, last_seen_at=ts), _make_card(id=2, last_seen_at=None)]
        stats = svc._compute_topic_stats(topic, cards, TODAY)
        assert stats.avg_days_since_seen == 10.0

    def test_days_until_exam(self):
        topic = _make_topic(exam_date=date(2026, 6, 20))
        stats = svc._compute_topic_stats(topic, [], TODAY)
        assert stats.days_until_exam == 5

    def test_days_until_exam_past(self):
        topic = _make_topic(exam_date=date(2026, 6, 10))
        stats = svc._compute_topic_stats(topic, [], TODAY)
        assert stats.days_until_exam == -5


# ── list_topics ────────────────────────────────────────────────────────────────

class TestListTopics:
    def test_returns_lean_list(self, mock_api):
        mock_api.list_topics.return_value = [
            _make_topic(id=1, name="A"),
            _make_topic(id=2, name="B"),
        ]
        result = svc.list_topics()
        assert len(result) == 2
        assert result[0].name == "A"
        assert result[1].name == "B"

    def test_empty(self, mock_api):
        mock_api.list_topics.return_value = []
        assert svc.list_topics() == []


# ── list_topics_overview ───────────────────────────────────────────────────────

class TestListTopicsOverview:
    def test_includes_stats(self, mock_api):
        topic = _make_topic(id=1, name="Physics")
        mock_api.list_topics.return_value = [topic]
        mock_api.list_cards_by_topic.return_value = [_make_card(memorized=True)]
        result = svc.list_topics_overview(TODAY)
        assert len(result) == 1
        assert result[0].stats.total_cards == 1
        assert result[0].stats.memorized_cards == 1

    def test_empty_topic_list(self, mock_api):
        mock_api.list_topics.return_value = []
        assert svc.list_topics_overview(TODAY) == []

    def test_none_cards_treated_as_empty(self, mock_api):
        topic = _make_topic(id=1)
        mock_api.list_topics.return_value = [topic]
        mock_api.list_cards_by_topic.return_value = None
        result = svc.list_topics_overview(TODAY)
        assert result[0].stats.total_cards == 0


# ── get_topic ──────────────────────────────────────────────────────────────────

class TestGetTopic:
    def test_existing(self, mock_api):
        mock_api.get_topic.return_value = _make_topic(id=1, name="Chem")
        mock_api.list_cards_by_topic.return_value = []
        result = svc.get_topic(1, TODAY)
        assert result is not None
        assert result.name == "Chem"

    def test_missing_returns_none(self, mock_api):
        mock_api.get_topic.return_value = None
        assert svc.get_topic(999, TODAY) is None


# ── create_topic ───────────────────────────────────────────────────────────────

class TestCreateTopic:
    def test_minimal(self, mock_api):
        mock_api.create_topics.return_value = _make_topic(id=1, name="History")
        mock_api.list_cards_by_topic.return_value = []
        data = TopicCreate(name="History")
        result = svc.create_topic(data, TODAY)
        assert result.name == "History"
        assert result.stats.total_cards == 0

    def test_full(self, mock_api):
        mock_api.create_topics.return_value = _make_topic(
            id=2, name="Bio", description="Life", exam_date=date(2026, 7, 1)
        )
        mock_api.list_cards_by_topic.return_value = []
        data = TopicCreate(name="Bio", description="Life", exam_date=date(2026, 7, 1))
        result = svc.create_topic(data, TODAY)
        assert result.description == "Life"
        assert result.stats.days_until_exam == 16

    def test_passes_correct_data_to_db(self, mock_api):
        mock_api.create_topics.return_value = _make_topic(id=3, name="Art")
        mock_api.list_cards_by_topic.return_value = []
        svc.create_topic(TopicCreate(name="Art"), TODAY)
        call_arg = mock_api.create_topics.call_args[0][0]
        assert call_arg.name == "Art"


# ── update_topic ───────────────────────────────────────────────────────────────

class TestUpdateTopic:
    def test_existing(self, mock_api):
        mock_api.update_topics.return_value = _make_topic(id=1, name="Updated")
        mock_api.list_cards_by_topic.return_value = []
        result = svc.update_topic(1, TopicUpdate(name="Updated"), TODAY)
        assert result is not None
        assert result.name == "Updated"

    def test_missing_returns_none(self, mock_api):
        mock_api.update_topics.return_value = None
        assert svc.update_topic(999, TopicUpdate(name="X"), TODAY) is None

    def test_passes_id_to_db(self, mock_api):
        mock_api.update_topics.return_value = _make_topic(id=5, name="X")
        mock_api.list_cards_by_topic.return_value = []
        svc.update_topic(5, TopicUpdate(name="X"), TODAY)
        call_arg = mock_api.update_topics.call_args[0][0]
        assert call_arg.id == 5


# ── delete_topic ───────────────────────────────────────────────────────────────

class TestDeleteTopic:
    def test_existing_returns_true(self, mock_api):
        mock_api.delete_topic.return_value = True
        assert svc.delete_topic(1) is True

    def test_missing_returns_false(self, mock_api):
        mock_api.delete_topic.return_value = False
        assert svc.delete_topic(999) is False


# ── list_topic_decks ───────────────────────────────────────────────────────────

class TestListTopicDecks:
    def test_returns_deck_list(self, mock_api):
        from app.database.schemas import DeckResponse as DbDeckResponse
        mock_api.list_decks_by_topic.return_value = [
            DbDeckResponse(id=1, name="D1", topic_id=1),
            DbDeckResponse(id=2, name="D2", topic_id=1),
        ]
        result = svc.list_topic_decks(1)
        assert result is not None
        assert len(result) == 2
        assert result[0].name == "D1"

    def test_missing_topic_returns_none(self, mock_api):
        mock_api.list_decks_by_topic.return_value = None
        assert svc.list_topic_decks(999) is None

    def test_empty_returns_empty_list(self, mock_api):
        mock_api.list_decks_by_topic.return_value = []
        assert svc.list_topic_decks(1) == []
