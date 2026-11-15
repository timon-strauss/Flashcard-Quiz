from datetime import datetime, timezone
from ..database import db
from ..database.schemas import DeckCreate as DbDeckCreate, DeckUpdate as DbDeckUpdate
from ..routers.schemas import DeckCreate, DeckUpdate, DeckLean, DeckResponse, DeckStats, CardResponse
from .image_service import delete_image


def _deck_stats(api, deck_id: int) -> DeckStats:
    stats = api.get_card_stats(datetime.now(timezone.utc), deck_id=deck_id)
    if stats is None:
        return DeckStats(
            total_cards=0, due_cards=0, new_cards=0,
            learning_cards=0, review_cards=0, relearning_cards=0,
        )
    return DeckStats(
        total_cards=stats.total,
        due_cards=stats.due,
        new_cards=stats.new,
        learning_cards=stats.learning,
        review_cards=stats.review,
        relearning_cards=stats.relearning,
        ready_cards=stats.ready,
        last_review=stats.last_review,
    )


def _to_response(deck, stats: DeckStats) -> DeckResponse:
    return DeckResponse.model_validate({**deck.model_dump(), "stats": stats})


def list_decks() -> list[DeckLean]:
    with db() as api:
        decks = api.list_decks()
    return [DeckLean.model_validate(d) for d in decks]


def list_decks_overview() -> list[DeckResponse]:
    with db() as api:
        decks = api.list_decks()
        return [_to_response(d, _deck_stats(api, d.id)) for d in decks]


def get_deck(deck_id: int) -> DeckResponse | None:
    with db() as api:
        d = api.get_deck(deck_id)
        if d is None:
            return None
        return _to_response(d, _deck_stats(api, deck_id))


def create_deck(data: DeckCreate) -> DeckResponse | None:
    db_data = DbDeckCreate.model_validate(data.model_dump())
    with db() as api:
        d = api.create_deck(db_data)
        if d is None:
            return None
        return _to_response(d, _deck_stats(api, d.id))


def update_deck(deck_id: int, data: DeckUpdate) -> DeckResponse | None:
    db_data = DbDeckUpdate.model_validate({"id": deck_id, **data.model_dump(exclude_unset=True)})
    with db() as api:
        d = api.update_deck(db_data)
        if d is None:
            return None
        return _to_response(d, _deck_stats(api, deck_id))


def delete_deck(deck_id: int) -> bool:
    with db() as api:
        cards = api.list_cards(deck_id=deck_id) or []
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
        cards = api.list_cards(deck_id=deck_id)
    if cards is None:
        return None
    return [CardResponse.model_validate(c) for c in cards]


def reorder_deck_cards(deck_id: int, card_ids: list[int]) -> list[CardResponse] | None:
    with db() as api:
        cards = api.reorder_cards(deck_id, card_ids)
    if cards is None:
        return None
    return [CardResponse.model_validate(c) for c in cards]
