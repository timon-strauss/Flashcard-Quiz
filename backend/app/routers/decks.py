from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=list[schemas.DeckRead])
def list_decks(db: Session = Depends(get_db)):
    return db.query(models.Deck).all()


@router.post("", response_model=schemas.DeckRead, status_code=status.HTTP_201_CREATED)
def create_deck(payload: schemas.DeckCreate, db: Session = Depends(get_db)):
    deck = models.Deck(**payload.model_dump())
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return deck


@router.get("/{deck_id}", response_model=schemas.DeckRead)
def get_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = db.get(models.Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.put("/{deck_id}", response_model=schemas.DeckRead)
def update_deck(deck_id: int, payload: schemas.DeckUpdate, db: Session = Depends(get_db)):
    deck = db.get(models.Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(deck, field, value)
    db.commit()
    db.refresh(deck)
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = db.get(models.Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    db.delete(deck)
    db.commit()


@router.get("/{deck_id}/cards", response_model=list[schemas.CardRead])
def list_cards(deck_id: int, db: Session = Depends(get_db)):
    deck = db.get(models.Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return db.query(models.Card).filter(models.Card.deck_id == deck_id).all()


@router.post("/{deck_id}/cards", response_model=schemas.CardRead, status_code=status.HTTP_201_CREATED)
def create_card(deck_id: int, payload: schemas.CardCreate, db: Session = Depends(get_db)):
    deck = db.get(models.Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    card = models.Card(deck_id=deck_id, **payload.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card
