from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.routers.schemas import TopicCreate, TopicUpdate
from app.database.schemas import (
    TopicResponse as DbTopicResponse, DeckResponse as DbDeckResponse,
    CardResponse as DbCardResponse, CardStats,
)
import app.services.topic_service as svc


TODAY = date(2026, 6, 15)


def _make_topic(id=1, name="Math", description=None, exam_date=None) -> DbTopicResponse:
    return DbTopicResponse(id=id, name=name, description=description, exam_date=exam_date)


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
    with patch("app.services.topic_service.db") as mock_db:
        mock_db.return_value.__enter__ = MagicMock(return_value=api)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        yield api


# ── stats ──────────────────────────────────────────────────────────────────────

class TestTopicStats:
    def test_empty_topic(self, mock_api):
        stats = svc._topic_stats(mock_api, _make_topic(), TODAY)
        assert stats.total_cards == 0
        assert stats.due_cards == 0
        assert stats.days_until_exam is None

    def test_maps_card_stats(self, mock_api):
        mock_api.get_card_stats.return_value = CardStats(
            total=10, due=4, new=3, learning=2, review=4, relearning=1
        )
        stats = svc._topic_stats(mock_api, _make_topic(), TODAY)
        assert stats.total_cards == 10
        assert stats.due_cards == 4
        assert stats.new_cards == 3
        assert stats.learning_cards == 2
        assert stats.review_cards == 4
        assert stats.relearning_cards == 1

    def test_asks_for_stats_of_that_topic_as_of_now(self, mock_api):
        before = datetime.now(timezone.utc)
        svc._topic_stats(mock_api, _make_topic(id=7), TODAY)
        args, kwargs = mock_api.get_card_stats.call_args
        assert kwargs == {"topic_id": 7}
        assert before <= args[0] <= datetime.now(timezone.utc)

    def test_missing_stats_treated_as_empty(self, mock_api):
        mock_api.get_card_stats.return_value = None
        assert svc._topic_stats(mock_api, _make_topic(), TODAY).total_cards == 0

    def test_days_until_exam(self, mock_api):
        topic = _make_topic(exam_date=date(2026, 6, 20))
        assert svc._topic_stats(mock_api, topic, TODAY).days_until_exam == 5

    def test_days_until_exam_past(self, mock_api):
        topic = _make_topic(exam_date=date(2026, 6, 10))
        assert svc._topic_stats(mock_api, topic, TODAY).days_until_exam == -5


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
        mock_api.list_topics.return_value = [_make_topic(id=1, name="Physics")]
        mock_api.get_card_stats.return_value = CardStats(total=1, due=1, new=1)
        result = svc.list_topics_overview(TODAY)
        assert len(result) == 1
        assert result[0].stats.total_cards == 1
        assert result[0].stats.due_cards == 1

    def test_empty_topic_list(self, mock_api):
        mock_api.list_topics.return_value = []
        assert svc.list_topics_overview(TODAY) == []


# ── get_topic ──────────────────────────────────────────────────────────────────

class TestGetTopic:
    def test_existing(self, mock_api):
        mock_api.get_topic.return_value = _make_topic(id=1, name="Chem")
        result = svc.get_topic(1, TODAY)
        assert result is not None
        assert result.name == "Chem"

    def test_missing_returns_none(self, mock_api):
        mock_api.get_topic.return_value = None
        assert svc.get_topic(999, TODAY) is None


# ── create_topic ───────────────────────────────────────────────────────────────

class TestCreateTopic:
    def test_minimal(self, mock_api):
        mock_api.create_topic.return_value = _make_topic(id=1, name="History")
        data = TopicCreate(name="History")
        result = svc.create_topic(data, TODAY)
        assert result.name == "History"
        assert result.stats.total_cards == 0

    def test_full(self, mock_api):
        mock_api.create_topic.return_value = _make_topic(
            id=2, name="Bio", description="Life", exam_date=date(2026, 7, 1)
        )
        data = TopicCreate(name="Bio", description="Life", exam_date=date(2026, 7, 1))
        result = svc.create_topic(data, TODAY)
        assert result.description == "Life"
        assert result.stats.days_until_exam == 16

    def test_passes_correct_data_to_db(self, mock_api):
        mock_api.create_topic.return_value = _make_topic(id=3, name="Art")
        svc.create_topic(TopicCreate(name="Art"), TODAY)
        call_arg = mock_api.create_topic.call_args[0][0]
        assert call_arg.name == "Art"


# ── update_topic ───────────────────────────────────────────────────────────────

class TestUpdateTopic:
    def test_existing(self, mock_api):
        mock_api.update_topic.return_value = _make_topic(id=1, name="Updated")
        result = svc.update_topic(1, TopicUpdate(name="Updated"), TODAY)
        assert result is not None
        assert result.name == "Updated"

    def test_missing_returns_none(self, mock_api):
        mock_api.update_topic.return_value = None
        assert svc.update_topic(999, TopicUpdate(name="X"), TODAY) is None

    def test_passes_id_to_db(self, mock_api):
        mock_api.update_topic.return_value = _make_topic(id=5, name="X")
        svc.update_topic(5, TopicUpdate(name="X"), TODAY)
        call_arg = mock_api.update_topic.call_args[0][0]
        assert call_arg.id == 5


# ── delete_topic ───────────────────────────────────────────────────────────────

class TestDeleteTopic:
    def test_existing_returns_true(self, mock_api):
        mock_api.delete_topic.return_value = True
        assert svc.delete_topic(1) is True

    def test_missing_returns_false(self, mock_api):
        mock_api.delete_topic.return_value = False
        assert svc.delete_topic(999) is False

    def test_deletes_card_images_of_all_decks(self, mock_api):
        mock_api.list_decks.return_value = [
            DbDeckResponse(id=1, name="D1", topic_id=1),
            DbDeckResponse(id=2, name="D2", topic_id=1),
        ]
        mock_api.list_cards.side_effect = lambda deck_id: [
            _make_card(id=deck_id, deck_id=deck_id, front_image=f"f{deck_id}.png")
        ]
        mock_api.delete_topic.return_value = True
        with patch("app.services.topic_service.delete_image") as delete_image:
            svc.delete_topic(1)
        assert {c.args[0] for c in delete_image.call_args_list} == {"f1.png", "f2.png"}


# ── list_topic_decks ───────────────────────────────────────────────────────────

class TestListTopicDecks:
    def test_returns_deck_list(self, mock_api):
        mock_api.list_decks.return_value = [
            DbDeckResponse(id=1, name="D1", topic_id=1),
            DbDeckResponse(id=2, name="D2", topic_id=1),
        ]
        result = svc.list_topic_decks(1)
        assert result is not None
        assert len(result) == 2
        assert result[0].name == "D1"

    def test_missing_topic_returns_none(self, mock_api):
        mock_api.list_decks.return_value = None
        assert svc.list_topic_decks(999) is None

    def test_empty_returns_empty_list(self, mock_api):
        mock_api.list_decks.return_value = []
        assert svc.list_topic_decks(1) == []
