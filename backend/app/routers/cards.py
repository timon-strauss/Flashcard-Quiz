from fastapi import APIRouter
from .schemas import CardUpdate, CardMemorizedUpdate, CardResponse, _not_implemented

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: int):
    _not_implemented()


@router.put("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, body: CardUpdate):
    _not_implemented()


@router.delete("/{card_id}")
def delete_card(card_id: int):
    _not_implemented()


@router.patch("/{card_id}/seen", response_model=CardResponse)
def mark_card_seen(card_id: int):
    _not_implemented()


@router.patch("/{card_id}/memorized", response_model=CardResponse)
def set_card_memorized(card_id: int, body: CardMemorizedUpdate):
    _not_implemented()
