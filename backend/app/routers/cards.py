from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from .schemas import CardCreate, CardUpdate, CardMemorizedUpdate, CardResponse
from ..services import card_service
from ..services.image_service import save_image

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("", response_model=CardResponse)
async def create_card(
    deck_id: int = Form(...),
    front: str = Form(...),
    back: str = Form(...),
    front_image: Optional[UploadFile] = File(None),
    back_image: Optional[UploadFile] = File(None),
):
    front_image_name = None
    back_image_name = None
    if front_image:
        front_image_name = save_image(front_image, await front_image.read())
    if back_image:
        back_image_name = save_image(back_image, await back_image.read())

    body = CardCreate(
        deck_id=deck_id,
        front=front,
        back=back,
        front_image=front_image_name,
        back_image=back_image_name,
    )
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
