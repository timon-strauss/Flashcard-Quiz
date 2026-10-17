from datetime import datetime, timezone
from ..database import db
from ..database.schemas import CardCreate as DbCardCreate, CardUpdate as DbCardUpdate
from ..routers.schemas import CardCreate, CardUpdate, CardMemorizedUpdate, CardResponse
from .image_service import delete_image


def get_card(card_id: int) -> CardResponse | None:
    with db() as api:
        c = api.get_card(card_id)
    if c is None:
        return None
    return CardResponse.model_validate(c)


def create_card(data: CardCreate) -> CardResponse | None:
    db_data = DbCardCreate.model_validate(data.model_dump())
    with db() as api:
        c = api.create_card(db_data)
    if c is None:
        return None
    return CardResponse.model_validate(c)


def update_card(card_id: int, data: CardUpdate) -> CardResponse | None:
    updates = data.model_dump(exclude_unset=True)
    with db() as api:
        existing = api.get_card(card_id)
        if existing is None:
            return None
        old_front = existing.front_image
        old_back = existing.back_image
        db_data = DbCardUpdate.model_validate({"id": card_id, **updates})
        c = api.update_card(db_data)
    if c is None:
        return None
    if "front_image" in updates and updates["front_image"] != old_front and old_front:
        delete_image(old_front)
    if "back_image" in updates and updates["back_image"] != old_back and old_back:
        delete_image(old_back)
    return CardResponse.model_validate(c)


def delete_card(card_id: int) -> bool:
    with db() as api:
        card = api.get_card(card_id)
        if card is None:
            return False
        front_image = card.front_image
        back_image = card.back_image
        result = api.delete_card(card_id)
    if result:
        if front_image:
            delete_image(front_image)
        if back_image:
            delete_image(back_image)
    return result


def mark_card_seen(card_id: int) -> CardResponse | None:
    db_data = DbCardUpdate.model_validate({"id": card_id, "last_seen_at": datetime.now(timezone.utc)})
    with db() as api:
        c = api.update_card(db_data)
    if c is None:
        return None
    return CardResponse.model_validate(c)


def set_card_memorized(card_id: int, data: CardMemorizedUpdate) -> CardResponse | None:
    db_data = DbCardUpdate.model_validate({"id": card_id, "memorized": data.memorized})
    with db() as api:
        c = api.update_card(db_data)
    if c is None:
        return None
    return CardResponse.model_validate(c)
