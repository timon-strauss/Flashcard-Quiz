from datetime import date
from ..database import db
from ..database.schemas import DeckCreate as DbDeckCreate, DeckUpdate as DbDeckUpdate
from ..routers.schemas import DeckCreate, DeckUpdate, DeckLean, DeckResponse, DeckStats, CardResponse
from .image_service import delete_image


def _compute_deck_stats(cards) -> DeckStats:
    today = date.today()
    total = len(cards)
    memorized = sum(1 for c in cards if c.memorized)
    seen = [c.last_seen_at for c in cards if c.last_seen_at is not None]
    avg_days = sum((today - s.date()).days for s in seen) / len(seen) if seen else None
    return DeckStats(total_cards=total, memorized_cards=memorized, avg_days_since_seen=avg_days)


def _to_response(deck, cards) -> DeckResponse:
    stats = _compute_deck_stats(cards)
    return DeckResponse.model_validate({**deck.model_dump(), "stats": stats})


def list_decks() -> list[DeckLean]:
    with db() as api:
        decks = api.list_decks()
    return [DeckLean.model_validate(d) for d in decks]


def list_decks_overview() -> list[DeckResponse]:
    with db() as api:
        decks = api.list_decks()
        deck_cards = {d.id: api.list_cards_by_deck(d.id) or [] for d in decks}
    return [_to_response(d, deck_cards[d.id]) for d in decks]


def get_deck(deck_id: int) -> DeckResponse | None:
    with db() as api:
        d = api.get_deck(deck_id)
        if d is None:
            return None
        cards = api.list_cards_by_deck(deck_id) or []
    return _to_response(d, cards)


def create_deck(data: DeckCreate) -> DeckResponse | None:
    db_data = DbDeckCreate.model_validate(data.model_dump())
    with db() as api:
        d = api.create_deck(db_data)
        if d is None:
            return None
        cards = api.list_cards_by_deck(d.id) or []
    return _to_response(d, cards)


def update_deck(deck_id: int, data: DeckUpdate) -> DeckResponse | None:
    db_data = DbDeckUpdate.model_validate({"id": deck_id, **data.model_dump(exclude_unset=True)})
    with db() as api:
        d = api.update_deck(db_data)
        if d is None:
            return None
        cards = api.list_cards_by_deck(deck_id) or []
    return _to_response(d, cards)


def delete_deck(deck_id: int) -> bool:
    with db() as api:
        cards = api.list_cards_by_deck(deck_id) or []
        images = [(c.front_image, c.back_image) for c in cards]
        result = api.delete_deck(deck_id)
    if result:
        for front_image, back_image in images:
            if front_image:
                delete_image(front_image)
            if back_image:
                delete_image(back_image)
    return result


def list_deck_cards(deck_id: int) -> list[CardResponse] | None:
    with db() as api:
        cards = api.list_cards_by_deck(deck_id)
    if cards is None:
        return None
    return [CardResponse.model_validate(c) for c in cards]


def reorder_deck_cards(deck_id: int, card_ids: list[int]) -> list[CardResponse] | None:
    with db() as api:
        cards = api.reorder_cards(deck_id, card_ids)
    if cards is None:
        return None
    return [CardResponse.model_validate(c) for c in cards]
