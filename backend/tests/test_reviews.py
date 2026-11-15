from datetime import datetime, timedelta, timezone

import pytest

from app.database.schemas import TopicCreate, DeckCreate, CardCreate, CardReview, CardStats

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)

LEARNING, REVIEW, RELEARNING = 1, 2, 3
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


@pytest.fixture
def deck(api):
    return api.create_deck(DeckCreate(name="Default Deck"))


@pytest.fixture
def topic_deck(api):
    """A deck that belongs to a topic."""
    topic = api.create_topic(TopicCreate(name="Topic"))
    return api.create_deck(DeckCreate(name="Topic Deck", topic_id=topic.id))


def _card(api, deck, front="Q"):
    return api.create_card(CardCreate(front=front, back="A", deck_id=deck.id))


def _review(api, card, rating=GOOD, at=NOW, state=REVIEW, step=None, due=None,
            stability=3.5, difficulty=5.0):
    return api.review_card(CardReview(
        card_id=card.id, rating=rating, reviewed_at=at,
        state=state, step=step, stability=stability, difficulty=difficulty,
        due=due if due is not None else at + 3 * DAY,
    ))


class TestReviewCard:
    def test_stores_new_scheduling_state(self, api, deck):
        card = _card(api, deck)
        result = _review(api, card, state=LEARNING, step=1, stability=2.3, difficulty=4.2,
                         due=NOW + timedelta(minutes=10))
        assert result.state == LEARNING
        assert result.step == 1
        assert result.stability == 2.3
        assert result.difficulty == 4.2
        assert result.due == NOW + timedelta(minutes=10)
        assert result.last_review == NOW

    def test_state_is_persisted(self, api, deck):
        card = _card(api, deck)
        result = _review(api, card)
        assert api.get_card(card.id) == result

    def test_step_is_cleared_when_card_graduates(self, api, deck):
        card = _card(api, deck)
        assert _review(api, card, state=REVIEW, step=None).step is None

    def test_keeps_content(self, api, deck):
        card = _card(api, deck, front="Front")
        result = _review(api, card)
        assert result.front == "Front"
        assert result.deck_id == deck.id
        assert result.position == card.position

    def test_writes_review_log(self, api, deck):
        card = _card(api, deck)
        _review(api, card, rating=HARD)
        logs = api.list_review_logs(card_id=card.id)
        assert len(logs) == 1
        assert logs[0].card_id == card.id
        assert logs[0].rating == HARD
        assert logs[0].reviewed_at == NOW

    def test_each_review_adds_a_log(self, api, deck):
        card = _card(api, deck)
        _review(api, card, rating=AGAIN, at=NOW)
        _review(api, card, rating=GOOD, at=NOW + DAY)
        assert [log.rating for log in api.list_review_logs(card_id=card.id)] == [AGAIN, GOOD]

    def test_missing_card_returns_none_and_writes_no_log(self, api):
        result = api.review_card(CardReview(
            card_id=999, rating=GOOD, reviewed_at=NOW,
            state=REVIEW, stability=1.0, difficulty=1.0, due=NOW,
        ))
        assert result is None
        assert api.list_review_logs() == []

    def test_datetimes_are_returned_as_utc(self, api, deck):
        card = _card(api, deck)
        result = _review(api, card)
        assert result.due.tzinfo == timezone.utc
        assert result.last_review.tzinfo == timezone.utc
        assert api.list_review_logs(card_id=card.id)[0].reviewed_at.tzinfo == timezone.utc

    def test_other_timezones_are_converted_to_utc(self, api, deck):
        card = _card(api, deck)
        berlin = timezone(timedelta(hours=1))
        result = _review(api, card, at=NOW.astimezone(berlin),
                         due=(NOW + DAY).astimezone(berlin))
        assert result.last_review == NOW
        assert result.last_review.utcoffset() == timedelta(0)
        assert result.due == NOW + DAY
        assert result.due.utcoffset() == timedelta(0)

    def test_deleting_card_deletes_its_logs(self, api, deck):
        card = _card(api, deck)
        other = _card(api, deck)
        _review(api, card)
        _review(api, other)
        api.delete_card(card.id)
        assert [log.card_id for log in api.list_review_logs()] == [other.id]


class TestListDueCards:
    def test_empty(self, api):
        assert api.list_due_cards(NOW) == []

    def test_new_cards_are_due(self, api, deck):
        card = _card(api, deck)
        result = api.list_due_cards(datetime.now(timezone.utc))
        assert [c.id for c in result] == [card.id]

    def test_excludes_cards_due_later(self, api, deck):
        due = _card(api, deck)
        later = _card(api, deck)
        _review(api, due, due=NOW - DAY)
        _review(api, later, due=NOW + DAY)
        assert [c.id for c in api.list_due_cards(NOW)] == [due.id]

    def test_includes_card_due_exactly_now(self, api, deck):
        card = _card(api, deck)
        _review(api, card, due=NOW)
        assert [c.id for c in api.list_due_cards(NOW)] == [card.id]

    def test_most_overdue_first(self, api, deck):
        a = _card(api, deck)
        b = _card(api, deck)
        c = _card(api, deck)
        _review(api, a, due=NOW - 1 * DAY)
        _review(api, b, due=NOW - 3 * DAY)
        _review(api, c, due=NOW - 2 * DAY)
        assert [x.id for x in api.list_due_cards(NOW)] == [b.id, c.id, a.id]

    def test_limit(self, api, deck):
        a = _card(api, deck)
        b = _card(api, deck)
        _review(api, a, due=NOW - 1 * DAY)
        _review(api, b, due=NOW - 2 * DAY)
        assert [x.id for x in api.list_due_cards(NOW, limit=1)] == [b.id]

    def test_filter_by_deck(self, api, deck, topic_deck):
        mine = _card(api, deck)
        other = _card(api, topic_deck)
        _review(api, mine, due=NOW - DAY)
        _review(api, other, due=NOW - DAY)
        assert [c.id for c in api.list_due_cards(NOW, deck_id=deck.id)] == [mine.id]

    def test_filter_by_topic_spans_its_decks(self, api, deck, topic_deck):
        second = api.create_deck(DeckCreate(name="Second", topic_id=topic_deck.topic_id))
        a = _card(api, topic_deck)
        b = _card(api, second)
        standalone = _card(api, deck)
        _review(api, a, due=NOW - 2 * DAY)
        _review(api, b, due=NOW - 1 * DAY)
        _review(api, standalone, due=NOW - 3 * DAY)
        result = api.list_due_cards(NOW, topic_id=topic_deck.topic_id)
        assert [c.id for c in result] == [a.id, b.id]

    def test_missing_deck_returns_none(self, api):
        assert api.list_due_cards(NOW, deck_id=999) is None

    def test_missing_topic_returns_none(self, api):
        assert api.list_due_cards(NOW, topic_id=999) is None

    def test_due_before_in_other_timezone(self, api, deck):
        card = _card(api, deck)
        _review(api, card, due=NOW)
        berlin = timezone(timedelta(hours=1))
        # 12:30 Berlin time is 11:30 UTC, so a card due 12:00 UTC is not due yet
        assert api.list_due_cards(datetime(2026, 1, 15, 12, 30, tzinfo=berlin)) == []
        assert len(api.list_due_cards(datetime(2026, 1, 15, 13, 0, tzinfo=berlin))) == 1


class TestListReviewLogs:
    def test_empty(self, api):
        assert api.list_review_logs() == []

    def test_returns_all_oldest_first(self, api, deck):
        a = _card(api, deck)
        b = _card(api, deck)
        _review(api, a, at=NOW + 2 * DAY)
        _review(api, b, at=NOW)
        _review(api, a, at=NOW + DAY)
        logs = api.list_review_logs()
        assert [log.reviewed_at for log in logs] == [NOW, NOW + DAY, NOW + 2 * DAY]

    def test_filter_by_card(self, api, deck):
        a = _card(api, deck)
        b = _card(api, deck)
        _review(api, a)
        _review(api, b)
        logs = api.list_review_logs(card_id=a.id)
        assert [log.card_id for log in logs] == [a.id]

    def test_card_without_reviews_returns_empty_list(self, api, deck):
        assert api.list_review_logs(card_id=_card(api, deck).id) == []

    def test_filter_by_deck(self, api, deck, topic_deck):
        mine = _card(api, deck)
        other = _card(api, topic_deck)
        _review(api, mine)
        _review(api, other)
        assert [log.card_id for log in api.list_review_logs(deck_id=deck.id)] == [mine.id]

    def test_filter_by_topic(self, api, deck, topic_deck):
        in_topic = _card(api, topic_deck)
        standalone = _card(api, deck)
        _review(api, in_topic)
        _review(api, standalone)
        logs = api.list_review_logs(topic_id=topic_deck.topic_id)
        assert [log.card_id for log in logs] == [in_topic.id]

    def test_since_is_inclusive(self, api, deck):
        card = _card(api, deck)
        _review(api, card, at=NOW - DAY)
        _review(api, card, at=NOW)
        _review(api, card, at=NOW + DAY)
        logs = api.list_review_logs(since=NOW)
        assert [log.reviewed_at for log in logs] == [NOW, NOW + DAY]

    def test_missing_card_returns_none(self, api):
        assert api.list_review_logs(card_id=999) is None

    def test_missing_deck_returns_none(self, api):
        assert api.list_review_logs(deck_id=999) is None

    def test_missing_topic_returns_none(self, api):
        assert api.list_review_logs(topic_id=999) is None


class TestGetCardStats:
    def test_no_cards(self, api):
        assert api.get_card_stats(NOW) == CardStats()

    def test_empty_deck(self, api, deck):
        assert api.get_card_stats(NOW, deck_id=deck.id) == CardStats()

    def test_counts_per_state(self, api, deck):
        _card(api, deck)                                        # new
        _card(api, deck)                                        # new
        _review(api, _card(api, deck), state=LEARNING, step=1)  # learning
        _review(api, _card(api, deck), state=REVIEW)            # review
        _review(api, _card(api, deck), state=REVIEW)            # review
        _review(api, _card(api, deck), state=RELEARNING, step=0)
        stats = api.get_card_stats(NOW)
        assert stats.total == 6
        assert stats.new == 2
        assert stats.learning == 1
        assert stats.review == 2
        assert stats.relearning == 1
        assert stats.new + stats.learning + stats.review + stats.relearning == stats.total

    def test_counts_due(self, api, deck):
        _review(api, _card(api, deck), due=NOW - DAY)
        _review(api, _card(api, deck), due=NOW)
        _review(api, _card(api, deck), due=NOW + DAY)
        assert api.get_card_stats(NOW).due == 2
        assert api.get_card_stats(NOW + DAY).due == 3

    def test_new_cards_count_as_due(self, api, deck):
        _card(api, deck)
        stats = api.get_card_stats(datetime.now(timezone.utc))
        assert stats.new == 1
        assert stats.due == 1

    def test_filter_by_deck(self, api, deck, topic_deck):
        _card(api, deck)
        _card(api, deck)
        _card(api, topic_deck)
        assert api.get_card_stats(NOW, deck_id=deck.id).total == 2

    def test_filter_by_topic_spans_its_decks(self, api, deck, topic_deck):
        second = api.create_deck(DeckCreate(name="Second", topic_id=topic_deck.topic_id))
        _card(api, topic_deck)
        _review(api, _card(api, second), state=REVIEW)
        _card(api, deck)  # standalone, not counted
        stats = api.get_card_stats(NOW, topic_id=topic_deck.topic_id)
        assert stats.total == 2
        assert stats.new == 1
        assert stats.review == 1

    def test_missing_deck_returns_none(self, api):
        assert api.get_card_stats(NOW, deck_id=999) is None

    def test_missing_topic_returns_none(self, api):
        assert api.get_card_stats(NOW, topic_id=999) is None
