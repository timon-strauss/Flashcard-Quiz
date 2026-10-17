import base64
import os
import uuid
from datetime import datetime, timezone

from ..database import db
from ..database.schemas import (
    DeckCreate as DbDeckCreate,
    CardCreate as DbCardCreate,
    TopicCreate as DbTopicCreate,
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Upload")


def _image_to_base64(filename: str) -> str | None:
    if not filename:
        return None
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _base64_to_file(data_url: str) -> str | None:
    if not data_url or not data_url.startswith("data:"):
        return None
    try:
        header, b64 = data_url.split(",", 1)
        mime = header.split(":")[1].split(";")[0]
        ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
        ext = ext_map.get(mime, ".bin")
        filename = f"{uuid.uuid4()}{ext}"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(base64.b64decode(b64))
        return filename
    except Exception:
        return None


def _serialize_cards(cards) -> list[dict]:
    result = []
    for c in cards:
        result.append({
            "front": c.front,
            "back": c.back,
            "front_image": _image_to_base64(c.front_image),
            "back_image": _image_to_base64(c.back_image),
            "position": c.position,
        })
    return result


def export_deck(deck_id: int) -> dict | None:
    with db() as api:
        deck = api.get_deck(deck_id)
        if deck is None:
            return None
        cards = api.list_cards_by_deck(deck_id) or []
    return {
        "version": 1,
        "type": "deck",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "deck": {
            "name": deck.name,
            "description": deck.description,
            "cards": _serialize_cards(cards),
        },
    }


def export_topic(topic_id: int) -> dict | None:
    with db() as api:
        topic = api.get_topic(topic_id)
        if topic is None:
            return None
        decks = api.list_decks_by_topic(topic_id) or []
        decks_data = []
        for d in decks:
            cards = api.list_cards_by_deck(d.id) or []
            decks_data.append({
                "name": d.name,
                "description": d.description,
                "cards": _serialize_cards(cards),
            })
    return {
        "version": 1,
        "type": "topic",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "topic": {
            "name": topic.name,
            "description": topic.description,
            "exam_date": topic.exam_date.isoformat() if topic.exam_date else None,
            "decks": decks_data,
        },
    }


def _unique_deck_name(base_name: str, api) -> str:
    existing = {d.name for d in api.list_decks()}
    name = base_name
    counter = 2
    while name in existing:
        name = f"{base_name} ({counter})"
        counter += 1
    return name


def _unique_topic_name(base_name: str, api) -> str:
    existing = {t.name for t in api.list_topics()}
    name = base_name
    counter = 2
    while name in existing:
        name = f"{base_name} ({counter})"
        counter += 1
    return name


def _import_deck_data(deck_data: dict, topic_id: int | None, api) -> dict:
    name = _unique_deck_name(deck_data["name"], api)
    deck = api.create_deck(DbDeckCreate(name=name, description=deck_data.get("description"), topic_id=topic_id))
    cards_imported = 0
    for card in deck_data.get("cards", []):
        front_image = _base64_to_file(card.get("front_image"))
        back_image = _base64_to_file(card.get("back_image"))
        api.create_card(DbCardCreate(
            deck_id=deck.id,
            front=card["front"],
            back=card["back"],
            front_image=front_image,
            back_image=back_image,
        ))
        cards_imported += 1
    return {"deck_id": deck.id, "deck_name": name, "cards_imported": cards_imported}


def import_transfer(payload: dict, target_topic_id: int | None = None) -> dict:
    version = payload.get("version")
    if version != 1:
        raise ValueError(f"Unsupported export version: {version}")

    kind = payload.get("type")

    if kind == "deck":
        with db() as api:
            if target_topic_id is not None and api.get_topic(target_topic_id) is None:
                raise ValueError(f"Topic {target_topic_id} not found")
            result = _import_deck_data(payload["deck"], target_topic_id, api)
        return {"type": "deck", "created": result}

    elif kind == "topic" and target_topic_id is not None:
        # importing a full topic export into a single deck context is not allowed;
        # the caller must omit target_topic_id or use the topic import path
        raise ValueError(
            "Diese Datei enthält ein ganzes Thema (mehrere Decks). "
            "Importiere sie über das Dashboard, nicht über ein einzelnes Deck."
        )

    elif kind == "topic":
        topic_data = payload["topic"]
        with db() as api:
            if target_topic_id is not None:
                topic = api.get_topic(target_topic_id)
                if topic is None:
                    raise ValueError(f"Topic {target_topic_id} not found")
                topic_id = target_topic_id
                topic_name = topic.name
                decks_imported = []
                for deck_data in topic_data.get("decks", []):
                    decks_imported.append(_import_deck_data(deck_data, topic_id, api))
            else:
                from datetime import date
                exam_date = None
                if topic_data.get("exam_date"):
                    exam_date = date.fromisoformat(topic_data["exam_date"])
                topic_name = _unique_topic_name(topic_data["name"], api)
                new_topic = api.create_topics(DbTopicCreate(
                    name=topic_name,
                    description=topic_data.get("description"),
                    exam_date=exam_date,
                ))
                topic_id = new_topic.id
                decks_imported = []
                for deck_data in topic_data.get("decks", []):
                    decks_imported.append(_import_deck_data(deck_data, topic_id, api))
        return {
            "type": "topic",
            "created": {
                "topic_id": topic_id,
                "topic_name": topic_name,
                "decks_imported": decks_imported,
            },
        }

    else:
        raise ValueError(f"Unknown export type: {kind!r}")
