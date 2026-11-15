"""The HTTP endpoints, end to end against an in-memory database."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.main import app

AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


@pytest.fixture
def client(monkeypatch):
    # one shared connection, because the endpoints run in worker threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(
        "app.database.SQLlite.SessionLocal",
        sessionmaker(autocommit=False, autoflush=False, bind=engine),
    )
    # no "with": the startup hook would create the real database
    yield TestClient(app)
    engine.dispose()


def _topic(client, name="Topic", **extra):
    return client.post("/topics", json={"name": name, **extra}).json()


def _deck(client, name="Deck", topic_id=None):
    return client.post("/decks", json={"name": name, "topic_id": topic_id}).json()


def _card(client, deck, front="Q", back="A"):
    return client.post("/cards", data={"deck_id": deck["id"], "front": front, "back": back}).json()


def _review(client, card, rating):
    return client.post(f"/cards/{card['id']}/review", json={"rating": rating})


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class TestTopics:
    def test_create_and_get(self, client):
        response = client.post("/topics", json={"name": "Math", "exam_date": "2030-01-01"})
        assert response.status_code == 201
        topic = client.get(f"/topics/{response.json()['id']}").json()
        assert topic["name"] == "Math"
        assert topic["exam_date"] == "2030-01-01"
        assert topic["stats"]["days_until_exam"] > 0

    def test_list_and_overview(self, client):
        _topic(client, "A")
        _topic(client, "B")
        assert [t["name"] for t in client.get("/topics").json()] == ["A", "B"]
        assert all("stats" in t for t in client.get("/topics/overview").json())

    def test_update(self, client):
        topic = _topic(client, "Old")
        response = client.put(f"/topics/{topic['id']}", json={"name": "New"})
        assert response.json()["name"] == "New"

    def test_delete_removes_decks_and_cards(self, client):
        topic = _topic(client)
        deck = _deck(client, topic_id=topic["id"])
        card = _card(client, deck)
        assert client.delete(f"/topics/{topic['id']}").status_code == 204
        assert client.get(f"/decks/{deck['id']}").status_code == 404
        assert client.get(f"/cards/{card['id']}").status_code == 404

    def test_list_decks_of_topic(self, client):
        topic = _topic(client)
        _deck(client, "In topic", topic_id=topic["id"])
        _deck(client, "Standalone")
        decks = client.get(f"/topics/{topic['id']}/decks").json()
        assert [d["name"] for d in decks] == ["In topic"]

    def test_missing_topic_is_404(self, client):
        assert client.get("/topics/999").status_code == 404
        assert client.put("/topics/999", json={"name": "X"}).status_code == 404
        assert client.delete("/topics/999").status_code == 404
        assert client.get("/topics/999/decks").status_code == 404
        assert client.get("/topics/999/due-cards").status_code == 404

    def test_stats_count_cards_of_all_decks(self, client):
        topic = _topic(client)
        _card(client, _deck(client, "D1", topic_id=topic["id"]))
        _card(client, _deck(client, "D2", topic_id=topic["id"]))
        _card(client, _deck(client, "Standalone"))
        stats = client.get(f"/topics/{topic['id']}").json()["stats"]
        assert stats["total_cards"] == 2
        assert stats["new_cards"] == 2
        assert stats["due_cards"] == 2


class TestDecks:
    def test_create_and_get(self, client):
        response = client.post("/decks", json={"name": "Vocab", "description": "words"})
        assert response.status_code == 201
        deck = client.get(f"/decks/{response.json()['id']}").json()
        assert deck["name"] == "Vocab"
        assert deck["description"] == "words"
        assert deck["topic_id"] is None
        assert deck["stats"] == {
            "total_cards": 0, "due_cards": 0, "new_cards": 0,
            "learning_cards": 0, "review_cards": 0, "relearning_cards": 0,
        }

    def test_create_in_missing_topic_is_404(self, client):
        assert client.post("/decks", json={"name": "D", "topic_id": 999}).status_code == 404

    def test_list_and_overview(self, client):
        _deck(client, "A")
        _deck(client, "B")
        assert [d["name"] for d in client.get("/decks").json()] == ["A", "B"]
        assert all("stats" in d for d in client.get("/decks/overview").json())

    def test_update(self, client):
        deck = _deck(client, "Old")
        assert client.put(f"/decks/{deck['id']}", json={"name": "New"}).json()["name"] == "New"

    def test_delete_removes_cards(self, client):
        deck = _deck(client)
        card = _card(client, deck)
        assert client.delete(f"/decks/{deck['id']}").status_code == 204
        assert client.get(f"/cards/{card['id']}").status_code == 404

    def test_list_cards(self, client):
        deck = _deck(client)
        _card(client, deck, "Q1")
        _card(client, deck, "Q2")
        cards = client.get(f"/decks/{deck['id']}/cards").json()
        assert [c["front"] for c in cards] == ["Q1", "Q2"]

    def test_reorder_cards(self, client):
        deck = _deck(client)
        a = _card(client, deck, "Q1")
        b = _card(client, deck, "Q2")
        response = client.patch(f"/decks/{deck['id']}/card-order", json={"order": [b["id"], a["id"]]})
        assert [c["id"] for c in response.json()] == [b["id"], a["id"]]
        assert [c["id"] for c in client.get(f"/decks/{deck['id']}/cards").json()] == [b["id"], a["id"]]

    def test_missing_deck_is_404(self, client):
        assert client.get("/decks/999").status_code == 404
        assert client.put("/decks/999", json={"name": "X"}).status_code == 404
        assert client.delete("/decks/999").status_code == 404
        assert client.get("/decks/999/cards").status_code == 404
        assert client.get("/decks/999/due-cards").status_code == 404
        assert client.patch("/decks/999/card-order", json={"order": []}).status_code == 404


class TestCards:
    def test_create_returns_new_fsrs_card(self, client):
        deck = _deck(client)
        response = client.post("/cards", data={"deck_id": deck["id"], "front": "Q", "back": "A"})
        assert response.status_code == 201
        card = response.json()
        assert card["front"] == "Q"
        assert card["back"] == "A"
        assert card["state"] == 1
        assert card["step"] == 0
        assert card["stability"] is None
        assert card["difficulty"] is None
        assert card["last_review"] is None
        assert _parse(card["due"]) <= datetime.now(timezone.utc)

    def test_create_in_missing_deck_is_404(self, client):
        response = client.post("/cards", data={"deck_id": 999, "front": "Q", "back": "A"})
        assert response.status_code == 404

    def test_get(self, client):
        card = _card(client, _deck(client))
        assert client.get(f"/cards/{card['id']}").json() == card

    def test_update_content_keeps_schedule(self, client):
        card = _card(client, _deck(client))
        reviewed = _review(client, card, GOOD).json()
        updated = client.put(f"/cards/{card['id']}", data={"front": "New"}).json()
        assert updated["front"] == "New"
        assert updated["back"] == "A"
        assert updated["due"] == reviewed["due"]
        assert updated["state"] == reviewed["state"]

    def test_delete(self, client):
        card = _card(client, _deck(client))
        assert client.delete(f"/cards/{card['id']}").status_code == 204
        assert client.get(f"/cards/{card['id']}").status_code == 404

    def test_missing_card_is_404(self, client):
        assert client.get("/cards/999").status_code == 404
        assert client.put("/cards/999", data={"front": "X"}).status_code == 404
        assert client.delete("/cards/999").status_code == 404
        assert _review(client, {"id": 999}, GOOD).status_code == 404

    def test_old_endpoints_are_gone(self, client):
        card = _card(client, _deck(client))
        assert client.patch(f"/cards/{card['id']}/seen").status_code == 404
        assert client.patch(f"/cards/{card['id']}/memorized", json={"memorized": True}).status_code == 404


class TestReview:
    def test_good_schedules_next_learning_step(self, client):
        card = _card(client, _deck(client))
        before = datetime.now(timezone.utc)
        response = _review(client, card, GOOD)
        assert response.status_code == 200
        reviewed = response.json()
        assert reviewed["state"] == 1
        assert reviewed["step"] == 1
        assert reviewed["stability"] is not None
        assert reviewed["difficulty"] is not None
        assert _parse(reviewed["last_review"]) >= before
        assert _parse(reviewed["due"]) - _parse(reviewed["last_review"]) == timedelta(minutes=10)

    def test_easy_graduates_to_review(self, client):
        card = _card(client, _deck(client))
        reviewed = _review(client, card, EASY).json()
        assert reviewed["state"] == 2
        assert reviewed["step"] is None
        assert _parse(reviewed["due"]) - _parse(reviewed["last_review"]) >= timedelta(days=1)

    @pytest.mark.parametrize("rating", [0, 5, -1, "good", None])
    def test_invalid_rating_is_422(self, client, rating):
        card = _card(client, _deck(client))
        assert _review(client, card, rating).status_code == 422
        assert client.get(f"/cards/{card['id']}").json()["last_review"] is None

    def test_missing_rating_is_422(self, client):
        card = _card(client, _deck(client))
        assert client.post(f"/cards/{card['id']}/review", json={}).status_code == 422

    def test_review_updates_stats(self, client):
        deck = _deck(client)
        easy = _card(client, deck)
        again = _card(client, deck)
        _card(client, deck)
        _review(client, easy, EASY)
        _review(client, again, AGAIN)
        assert client.get(f"/decks/{deck['id']}").json()["stats"] == {
            "total_cards": 3,
            "due_cards": 1,       # only the untouched card; "again" is due in a minute
            "new_cards": 1,
            "learning_cards": 1,
            "review_cards": 1,
            "relearning_cards": 0,
        }


class TestDueCards:
    def test_new_cards_are_due_oldest_first(self, client):
        deck = _deck(client)
        a = _card(client, deck, "Q1")
        b = _card(client, deck, "Q2")
        due = client.get(f"/decks/{deck['id']}/due-cards").json()
        assert [c["id"] for c in due] == [a["id"], b["id"]]

    def test_reviewed_card_leaves_the_queue(self, client):
        deck = _deck(client)
        a = _card(client, deck, "Q1")
        b = _card(client, deck, "Q2")
        _review(client, a, GOOD)
        due = client.get(f"/decks/{deck['id']}/due-cards").json()
        assert [c["id"] for c in due] == [b["id"]]

    def test_deck_queue_only_has_its_own_cards(self, client):
        deck = _deck(client, "Mine")
        mine = _card(client, deck)
        _card(client, _deck(client, "Other"))
        due = client.get(f"/decks/{deck['id']}/due-cards").json()
        assert [c["id"] for c in due] == [mine["id"]]

    def test_topic_queue_spans_its_decks(self, client):
        topic = _topic(client)
        a = _card(client, _deck(client, "D1", topic_id=topic["id"]))
        b = _card(client, _deck(client, "D2", topic_id=topic["id"]))
        _card(client, _deck(client, "Standalone"))
        due = client.get(f"/topics/{topic['id']}/due-cards").json()
        assert [c["id"] for c in due] == [a["id"], b["id"]]

    def test_all_due_cards(self, client):
        topic = _topic(client)
        a = _card(client, _deck(client, "D1", topic_id=topic["id"]))
        b = _card(client, _deck(client, "Standalone"))
        assert [c["id"] for c in client.get("/cards/due").json()] == [a["id"], b["id"]]

    def test_all_due_cards_empty(self, client):
        assert client.get("/cards/due").json() == []

    def test_limit(self, client):
        deck = _deck(client)
        first = _card(client, deck, "Q1")
        _card(client, deck, "Q2")
        for url in (f"/decks/{deck['id']}/due-cards", "/cards/due"):
            assert [c["id"] for c in client.get(url, params={"limit": 1}).json()] == [first["id"]]

    def test_limit_must_be_positive(self, client):
        deck = _deck(client)
        assert client.get(f"/decks/{deck['id']}/due-cards", params={"limit": 0}).status_code == 422
        assert client.get("/cards/due", params={"limit": -1}).status_code == 422


class TestTransfer:
    def test_export_and_import_deck_starts_cards_as_new(self, client):
        deck = _deck(client, "Vocab")
        card = _card(client, deck)
        _review(client, card, EASY)
        exported = client.get(f"/export/deck/{deck['id']}")
        assert exported.status_code == 200
        response = client.post(
            "/import", files={"file": ("deck.json", exported.content, "application/json")}
        )
        assert response.status_code == 200
        created = response.json()["created"]
        assert created["deck_name"] == "Vocab (2)"
        imported = client.get(f"/decks/{created['deck_id']}/cards").json()
        assert [c["front"] for c in imported] == ["Q"]
        assert imported[0]["state"] == 1
        assert imported[0]["last_review"] is None

    def test_export_topic(self, client):
        topic = _topic(client, "Exam", exam_date="2030-01-01")
        _card(client, _deck(client, "D", topic_id=topic["id"]))
        data = client.get(f"/export/topic/{topic['id']}").json()
        assert data["topic"]["name"] == "Exam"
        assert [d["name"] for d in data["topic"]["decks"]] == ["D"]

    def test_export_missing_is_404(self, client):
        assert client.get("/export/deck/999").status_code == 404
        assert client.get("/export/topic/999").status_code == 404


class TestReviewHistory:
    def test_fills_days_without_reviews(self, client):
        days = client.get("/stats/reviews", params={"days": 7}).json()
        assert len(days) == 7
        assert all(d["total"] == 0 for d in days)
        assert days == sorted(days, key=lambda d: d["date"])

    def test_counts_todays_reviews_by_rating(self, client):
        deck = _deck(client)
        card = _card(client, deck)
        _review(client, card, AGAIN)
        _review(client, card, GOOD)
        _review(client, card, GOOD)
        today = client.get("/stats/reviews", params={"days": 3}).json()[-1]
        assert today["date"] == datetime.now(timezone.utc).date().isoformat()
        assert (today["total"], today["again"], today["hard"], today["good"], today["easy"]) == (3, 1, 0, 2, 0)

    def test_scoped_to_deck_and_topic(self, client):
        topic = _topic(client)
        inside = _deck(client, "In", topic_id=topic["id"])
        outside = _deck(client, "Out")
        _review(client, _card(client, inside), GOOD)
        _review(client, _card(client, outside), EASY)
        _review(client, _card(client, outside), EASY)

        def total(**scope):
            return client.get("/stats/reviews", params={"days": 1, **scope}).json()[0]["total"]

        assert total() == 3
        assert total(topic_id=topic["id"]) == 1
        assert total(deck_id=outside["id"]) == 2

    def test_unknown_scope_is_404(self, client):
        assert client.get("/stats/reviews", params={"deck_id": 999}).status_code == 404
        assert client.get("/stats/reviews", params={"topic_id": 999}).status_code == 404


class TestDueForecast:
    def test_fills_days_without_due_cards(self, client):
        days = client.get("/stats/due", params={"days": 7}).json()
        assert len(days) == 7
        assert all(d["count"] == 0 for d in days)
        assert days[0]["date"] == datetime.now(timezone.utc).date().isoformat()
        assert days == sorted(days, key=lambda d: d["date"])

    def test_new_cards_are_due_today(self, client):
        deck = _deck(client)
        _card(client, deck)
        _card(client, deck)
        days = client.get("/stats/due", params={"days": 3}).json()
        assert [d["count"] for d in days] == [2, 0, 0]

    def test_reviewed_card_moves_to_its_due_day(self, client):
        deck = _deck(client)
        card = _review(client, _card(client, deck), EASY).json()
        due = _parse(card["due"]).date()
        today = datetime.now(timezone.utc).date()
        assert due > today
        days = client.get("/stats/due", params={"days": (due - today).days + 1}).json()
        assert days[-1] == {"date": due.isoformat(), "count": 1}
        assert sum(d["count"] for d in days) == 1
        # outside the window the card is not counted at all
        assert sum(d["count"] for d in client.get("/stats/due", params={"days": 1}).json()) == 0

    def test_scoped_to_deck_and_topic(self, client):
        topic = _topic(client)
        inside = _deck(client, "In", topic_id=topic["id"])
        outside = _deck(client, "Out")
        _card(client, inside)
        _card(client, outside)
        _card(client, outside)

        def today(**scope):
            return client.get("/stats/due", params={"days": 1, **scope}).json()[0]["count"]

        assert today() == 3
        assert today(topic_id=topic["id"]) == 1
        assert today(deck_id=outside["id"]) == 2

    def test_unknown_scope_is_404(self, client):
        assert client.get("/stats/due", params={"deck_id": 999}).status_code == 404
        assert client.get("/stats/due", params={"topic_id": 999}).status_code == 404


class TestProgressHistory:
    def _known(self, client, **params):
        return [d["known"] for d in client.get("/stats/progress", params={"days": 2, **params}).json()]

    def test_empty_without_reviews(self, client):
        _card(client, _deck(client))
        days = client.get("/stats/progress", params={"days": 7}).json()
        assert len(days) == 7
        assert all(d["known"] == 0 for d in days)
        assert days[-1]["date"] == datetime.now(timezone.utc).date().isoformat()

    def test_counts_cards_last_rated_good_or_easy(self, client):
        deck = _deck(client)
        good, easy, hard, again = (_card(client, deck) for _ in range(4))
        _review(client, good, GOOD)
        _review(client, easy, EASY)
        _review(client, hard, HARD)
        _review(client, again, AGAIN)
        assert self._known(client) == [0, 2]

    def test_latest_rating_decides(self, client):
        deck = _deck(client)
        card = _card(client, deck)
        _review(client, card, GOOD)
        _review(client, card, AGAIN)
        assert self._known(client) == [0, 0]
        _review(client, card, GOOD)
        _review(client, card, GOOD)
        assert self._known(client) == [0, 1]

    def test_earlier_days_keep_their_count(self):
        from unittest.mock import MagicMock, patch
        from app.services import stats_service

        def log(card_id, rating, day, hour=12):
            return MagicMock(card_id=card_id, rating=rating,
                             reviewed_at=datetime(2030, 1, day, hour, tzinfo=timezone.utc))

        api = MagicMock()
        api.__enter__.return_value = api
        # card 1 known since before the window, card 2 wrong on the 2nd and right on the 3rd
        api.list_review_logs.return_value = [
            log(1, GOOD, 1), log(2, GOOD, 1), log(2, AGAIN, 2), log(2, GOOD, 3), log(1, HARD, 4),
        ]
        with patch.object(stats_service, "db", return_value=api):
            days = stats_service.progress_history(3, now=datetime(2030, 1, 4, 18, tzinfo=timezone.utc))
        assert [(d.date.day, d.known) for d in days] == [(2, 1), (3, 2), (4, 1)]

    def test_scoped_to_deck_and_topic(self, client):
        topic = _topic(client)
        inside = _deck(client, "In", topic_id=topic["id"])
        outside = _deck(client, "Out")
        _review(client, _card(client, inside), GOOD)
        _review(client, _card(client, outside), EASY)
        _review(client, _card(client, outside), EASY)
        assert self._known(client)[-1] == 3
        assert self._known(client, topic_id=topic["id"])[-1] == 1
        assert self._known(client, deck_id=outside["id"])[-1] == 2

    def test_unknown_scope_is_404(self, client):
        assert client.get("/stats/progress", params={"deck_id": 999}).status_code == 404
        assert client.get("/stats/progress", params={"topic_id": 999}).status_code == 404

