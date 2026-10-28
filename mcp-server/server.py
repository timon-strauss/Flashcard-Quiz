"""Read-only MCP server for the flashcard app.

Talks exclusively to the backend's HTTP API — it has no access to the
database or the Upload/ folder. Only GET requests are ever sent.
"""
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP, Image

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

mcp = FastMCP("Flashcards", host=MCP_HOST, port=MCP_PORT)
client = httpx.Client(base_url=BACKEND_URL, timeout=10.0)


def _get(path: str) -> Any:
    response = client.get(path)
    if response.status_code == 404:
        raise ValueError(response.json().get("detail", "Not found"))
    response.raise_for_status()
    return response.json()


# ── Topics ────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_topics() -> list[dict]:
    """List all topics (exams) including stats: total/memorized cards,
    average days since last seen and days until the exam."""
    return _get("/topics/overview")


@mcp.tool()
def get_topic(topic_id: int) -> dict:
    """Get a single topic with its stats."""
    return _get(f"/topics/{topic_id}")


@mcp.tool()
def list_topic_decks(topic_id: int) -> list[dict]:
    """List all decks belonging to a topic."""
    return _get(f"/topics/{topic_id}/decks")


# ── Decks ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_decks() -> list[dict]:
    """List all decks (with or without topic) including their stats."""
    return _get("/decks/overview")


@mcp.tool()
def get_deck(deck_id: int) -> dict:
    """Get a single deck with its stats."""
    return _get(f"/decks/{deck_id}")


@mcp.tool()
def list_deck_cards(deck_id: int) -> list[dict]:
    """List all cards of a deck (front, back, image filenames, memorized,
    last_seen_at, position)."""
    return _get(f"/decks/{deck_id}/cards")


# ── Cards ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_card(card_id: int) -> dict:
    """Get a single card."""
    return _get(f"/cards/{card_id}")


@mcp.tool()
def get_card_image(filename: str) -> Image:
    """Fetch an image referenced by a card (front_image / back_image)."""
    if "/" in filename or "\\" in filename or filename.startswith("."):
        raise ValueError("Invalid filename")
    response = client.get(f"/uploads/{filename}")
    if response.status_code == 404:
        raise ValueError("Image not found")
    response.raise_for_status()
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    return Image(data=response.content, format="jpeg" if ext == "jpg" else ext)


# ── Everything ────────────────────────────────────────────────────────────────

@mcp.tool()
def get_all_content() -> dict:
    """Return the complete content in one call: all topics with their decks
    and cards, plus decks that do not belong to any topic."""
    topics = _get("/topics/overview")
    decks = _get("/decks/overview")
    for deck in decks:
        deck["cards"] = _get(f"/decks/{deck['id']}/cards")
    for topic in topics:
        topic["decks"] = [d for d in decks if d["topic_id"] == topic["id"]]
    return {
        "topics": topics,
        "decks_without_topic": [d for d in decks if d["topic_id"] is None],
    }


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)
