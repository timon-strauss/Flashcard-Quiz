"""The review service against a real (in-memory) database and the real FSRS scheduler."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fsrs import Scheduler

from app.database.schemas import TopicCreate, DeckCreate, CardCreate
import app.services.review_service as svc

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
MINUTE = timedelta(minutes=1)
DAY = timedelta(days=1)

LEARNING, REVIEW, RELEARNING = 1, 2, 3
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


@pytest.fixture(autouse=True)
def service_db(api):
    """Lets the service use the in-memory database, with a scheduler without random fuzz."""
    with patch("app.services.review_service.db") as mock_db, \
         patch("app.services.review_service.scheduler", Scheduler(enable_fuzzing=False)):
        mock_db.return_value.__enter__ = MagicMock(return_value=api)
        mock_db.return_value.__exit__ = MagicMock(return_value=False)
        yield


@pytest.fixture
def deck(api):
    return api.create_deck(DeckCreate(name="Deck"))


@pytest.fixture
def card(api, deck):
    return api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))


class TestReviewCard:
    def test_missing_card_returns_none(self):
        assert svc.review_card(999, GOOD, NOW) is None

    def test_first_good_moves_to_next_learning_step(self, card):
        result = svc.review_card(card.id, GOOD, NOW)
        assert result.state == LEARNING
        assert result.step == 1
        assert result.due == NOW + 10 * MINUTE
        assert result.last_review == NOW
        assert result.stability is not None
        assert result.difficulty is not None

    def test_again_repeats_first_step(self, card):
        result = svc.review_card(card.id, AGAIN, NOW)
        assert result.state == LEARNING
        assert result.step == 0
        assert result.due == NOW + MINUTE

    def test_easy_graduates_immediately(self, card):
        result = svc.review_card(card.id, EASY, NOW)
        assert result.state == REVIEW
        assert result.step is None
        assert result.due >= NOW + DAY

    def test_two_goods_graduate_to_review(self, card):
        svc.review_card(card.id, GOOD, NOW)
        result = svc.review_card(card.id, GOOD, NOW + 10 * MINUTE)
        assert result.state == REVIEW
        assert result.step is None
        assert result.due >= NOW + DAY

    def test_forgetting_a_review_card_starts_relearning(self, card):
        graduated = svc.review_card(card.id, EASY, NOW)
        result = svc.review_card(card.id, AGAIN, graduated.due)
        assert result.state == RELEARNING
        assert result.step == 0
        assert result.due == graduated.due + 10 * MINUTE

    def test_better_rating_gives_longer_interval(self, api, deck):
        dues = {}
        for rating in (HARD, GOOD, EASY):
            c = api.create_card(CardCreate(front="Q", back="A", deck_id=deck.id))
            graduated = svc.review_card(c.id, EASY, NOW)
            dues[rating] = svc.review_card(c.id, rating, graduated.due).due
        assert dues[HARD] < dues[GOOD] < dues[EASY]

    def test_result_is_persisted(self, api, card):
        result = svc.review_card(card.id, GOOD, NOW)
        stored = api.get_card(card.id)
        assert stored.state == result.state
        assert stored.step == result.step
        assert stored.due == result.due
        assert stored.stability == result.stability
        assert stored.difficulty == result.difficulty

    def test_writes_review_log(self, api, card):
        svc.review_card(card.id, HARD, NOW)
        svc.review_card(card.id, GOOD, NOW + 10 * MINUTE)
        logs = api.list_review_logs(card_id=card.id)
        assert [(log.rating, log.reviewed_at) for log in logs] == [
            (HARD, NOW), (GOOD, NOW + 10 * MINUTE),
        ]

    def test_keeps_card_content(self, card):
        result = svc.review_card(card.id, GOOD, NOW)
        assert result.front == "Q"
        assert result.back == "A"

    def test_defaults_to_current_time(self, card):
        before = datetime.now(timezone.utc)
        result = svc.review_card(card.id, GOOD)
        assert before <= result.last_review <= datetime.now(timezone.utc)

    def test_invalid_rating_raises(self, api, card):
        with pytest.raises(ValueError):
            svc.review_card(card.id, 5, NOW)
        assert api.list_review_logs(card_id=card.id) == []


class TestListDueCards:
    def test_new_card_is_due(self, card):
        assert [c.id for c in svc.list_due_cards()] == [card.id]

    def test_reviewed_card_leaves_the_queue_until_due(self, card):
        reviewed = svc.review_card(card.id, GOOD, NOW)
        assert svc.list_due_cards(now=NOW) == []
        assert [c.id for c in svc.list_due_cards(now=reviewed.due)] == [card.id]

    def test_filter_by_deck(self, api, deck, card):
        other = api.create_deck(DeckCreate(name="Other"))
        api.create_card(CardCreate(front="Q2", back="A2", deck_id=other.id))
        assert [c.id for c in svc.list_due_cards(deck_id=deck.id)] == [card.id]

    def test_filter_by_topic(self, api, card):
        topic = api.create_topic(TopicCreate(name="T"))
        topic_deck = api.create_deck(DeckCreate(name="In topic", topic_id=topic.id))
        in_topic = api.create_card(CardCreate(front="Q2", back="A2", deck_id=topic_deck.id))
        assert [c.id for c in svc.list_due_cards(topic_id=topic.id)] == [in_topic.id]

    def test_limit(self, api, deck, card):
        api.create_card(CardCreate(front="Q2", back="A2", deck_id=deck.id))
        assert len(svc.list_due_cards(limit=1)) == 1

    def test_missing_deck_returns_none(self):
        assert svc.list_due_cards(deck_id=999) is None

    def test_missing_topic_returns_none(self):
        assert svc.list_due_cards(topic_id=999) is None
