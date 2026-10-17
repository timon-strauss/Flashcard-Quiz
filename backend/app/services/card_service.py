from datetime import datetime, timezone
from ..database import db
from ..database.schemas import CardCreate as DbCardCreate, CardUpdate as DbCardUpdate
from ..routers.schemas import CardCreate, CardUpdate, CardMemorizedUpdate, CardResponse


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
    db_data = DbCardUpdate.model_validate({"id": card_id, **data.model_dump(exclude_unset=True)})
    with db() as api:
        c = api.update_card(db_data)
    if c is None:
        return None
    return CardResponse.model_validate(c)


def delete_card(card_id: int) -> bool:
    with db() as api:
        return api.delete_card(card_id)


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
