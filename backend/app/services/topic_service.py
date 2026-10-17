from datetime import date
from ..database import db
from ..database.schemas import TopicCreate as DbTopicCreate, TopicUpdate as DbTopicUpdate
from ..routers.schemas import TopicCreate, TopicUpdate, TopicLean, TopicResponse, TopicStats, DeckLean
from .image_service import delete_image


def _compute_topic_stats(topic, cards, today: date) -> TopicStats:
    total = len(cards)
    memorized = sum(1 for c in cards if c.memorized)

    seen = [c.last_seen_at for c in cards if c.last_seen_at is not None]
    avg_days = sum((today - s.date()).days for s in seen) / len(seen) if seen else None

    days_until_exam = None
    if topic.exam_date:
        exam = topic.exam_date if isinstance(topic.exam_date, date) else topic.exam_date.date()
        days_until_exam = (exam - today).days

    return TopicStats(
        total_cards=total,
        memorized_cards=memorized,
        avg_days_since_seen=avg_days,
        days_until_exam=days_until_exam,
    )


def _to_response(topic, cards, today: date) -> TopicResponse:
    stats = _compute_topic_stats(topic, cards, today)
    return TopicResponse.model_validate({**topic.model_dump(), "stats": stats})


def list_topics() -> list[TopicLean]:
    with db() as api:
        topics = api.list_topics()
    return [TopicLean.model_validate(t) for t in topics]


def list_topics_overview(today: date) -> list[TopicResponse]:
    with db() as api:
        topics = api.list_topics()
        topic_cards = {t.id: api.list_cards_by_topic(t.id) or [] for t in topics}
    return [_to_response(t, topic_cards[t.id], today) for t in topics]


def get_topic(topic_id: int, today: date) -> TopicResponse | None:
    with db() as api:
        t = api.get_topic(topic_id)
        if t is None:
            return None
        cards = api.list_cards_by_topic(topic_id) or []
    return _to_response(t, cards, today)


def create_topic(data: TopicCreate, today: date) -> TopicResponse:
    db_data = DbTopicCreate.model_validate(data.model_dump())
    with db() as api:
        t = api.create_topics(db_data)
        cards = api.list_cards_by_topic(t.id) or []
    return _to_response(t, cards, today)


def update_topic(topic_id: int, data: TopicUpdate, today: date) -> TopicResponse | None:
    db_data = DbTopicUpdate.model_validate({"id": topic_id, **data.model_dump(exclude_unset=True)})
    with db() as api:
        t = api.update_topics(db_data)
        if t is None:
            return None
        cards = api.list_cards_by_topic(topic_id) or []
    return _to_response(t, cards, today)


def delete_topic(topic_id: int) -> bool:
    with db() as api:
        cards = api.list_cards_by_topic(topic_id) or []
        images = [(c.front_image, c.back_image) for c in cards]
        result = api.delete_topic(topic_id)
    if result:
        for front_image, back_image in images:
            if front_image:
                delete_image(front_image)
            if back_image:
                delete_image(back_image)
    return result


def list_topic_decks(topic_id: int) -> list[DeckLean] | None:
    with db() as api:
        decks = api.list_decks_by_topic(topic_id)
    if decks is None:
        return None
    return [DeckLean.model_validate(d) for d in decks]
