from fastapi import APIRouter, HTTPException, Query
from .schemas import DeckCreate, DeckUpdate, DeckLean, DeckResponse, CardResponse, CardOrderUpdate
from ..services import deck_service, review_service

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=list[DeckLean])
def list_decks():
    return deck_service.list_decks()


@router.get("/overview", response_model=list[DeckResponse])
def list_decks_overview():
    return deck_service.list_decks_overview()


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int):
    deck = deck_service.get_deck(deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden")
    return deck


@router.post("", response_model=DeckResponse, status_code=201)
def create_deck(body: DeckCreate):
    deck = deck_service.create_deck(body)
    if deck is None:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return deck


@router.put("/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, body: DeckUpdate):
    deck = deck_service.update_deck(deck_id, body)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden")
    return deck


@router.delete("/{deck_id}", status_code=204)
def delete_deck(deck_id: int):
    if not deck_service.delete_deck(deck_id):
        raise HTTPException(status_code=404, detail="Deck nicht gefunden")


@router.get("/{deck_id}/cards", response_model=list[CardResponse])
def list_deck_cards(deck_id: int):
    cards = deck_service.list_deck_cards(deck_id)
    if cards is None:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden")
    return cards


@router.patch("/{deck_id}/card-order", response_model=list[CardResponse])
def reorder_deck_cards(deck_id: int, body: CardOrderUpdate):
    cards = deck_service.reorder_deck_cards(deck_id, body.order)
    if cards is None:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden")
    return cards


@router.get("/{deck_id}/due-cards", response_model=list[CardResponse])
def list_due_deck_cards(deck_id: int, limit: int | None = Query(None, ge=1)):
    """The deck's cards to study now, most overdue first."""
    cards = review_service.list_due_cards(deck_id=deck_id, limit=limit)
    if cards is None:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden")
    return cards
