from fastapi import APIRouter
from .schemas import DeckCreate, DeckUpdate, DeckLean, DeckResponse, CardCreate, CardResponse, _not_implemented

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=list[DeckLean])
def list_decks():
    _not_implemented()


@router.get("/overview", response_model=list[DeckResponse])
def list_decks_overview():
    _not_implemented()


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int):
    _not_implemented()


@router.post("", response_model=DeckResponse)
def create_deck(body: DeckCreate):
    _not_implemented()


@router.put("/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, body: DeckUpdate):
    _not_implemented()


@router.delete("/{deck_id}")
def delete_deck(deck_id: int):
    _not_implemented()


@router.get("/{deck_id}/cards", response_model=list[CardResponse])
def list_deck_cards(deck_id: int):
    _not_implemented()


@router.post("/{deck_id}/cards", response_model=CardResponse)
def create_card(deck_id: int, body: CardCreate):
    _not_implemented()
