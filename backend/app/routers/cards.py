from fastapi import APIRouter, HTTPException
from .schemas import CardCreate, CardUpdate, CardMemorizedUpdate, CardResponse
from ..services import card_service

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardResponse)
def create_card(body: CardCreate):
    card = card_service.create_card(body)
    if card is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return card


@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: int):
    card = card_service.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.put("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, body: CardUpdate):
    card = card_service.update_card(card_id, body)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.delete("/{card_id}")
def delete_card(card_id: int):
    if not card_service.delete_card(card_id):
        raise HTTPException(status_code=404, detail="Card not found")


@router.patch("/{card_id}/seen", response_model=CardResponse)
def mark_card_seen(card_id: int):
    card = card_service.mark_card_seen(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@router.patch("/{card_id}/memorized", response_model=CardResponse)
def set_card_memorized(card_id: int, body: CardMemorizedUpdate):
    card = card_service.set_card_memorized(card_id, body)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card
