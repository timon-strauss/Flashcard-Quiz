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
