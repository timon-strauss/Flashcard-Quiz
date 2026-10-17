from fastapi import APIRouter, HTTPException
from .schemas import DeckCreate, DeckUpdate, DeckLean, DeckResponse, CardResponse
from ..services import deck_service

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
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.post("", response_model=DeckResponse)
def create_deck(body: DeckCreate):
    deck = deck_service.create_deck(body)
    if deck is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return deck


@router.put("/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, body: DeckUpdate):
    deck = deck_service.update_deck(deck_id, body)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.delete("/{deck_id}")
def delete_deck(deck_id: int):
    if not deck_service.delete_deck(deck_id):
        raise HTTPException(status_code=404, detail="Deck not found")


@router.get("/{deck_id}/cards", response_model=list[CardResponse])
def list_deck_cards(deck_id: int):
    cards = deck_service.list_deck_cards(deck_id)
    if cards is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return cards
