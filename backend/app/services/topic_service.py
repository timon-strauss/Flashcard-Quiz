from datetime import date, datetime, timezone
from ..database import db
from ..database.schemas import TopicCreate as DbTopicCreate, TopicUpdate as DbTopicUpdate
from ..routers.schemas import TopicCreate, TopicUpdate, TopicLean, TopicResponse, TopicStats, DeckLean
from .image_service import delete_image


def _topic_stats(api, topic, today: date) -> TopicStats:
    stats = api.get_card_stats(datetime.now(timezone.utc), topic_id=topic.id)

    days_until_exam = None
    if topic.exam_date:
        exam = topic.exam_date if isinstance(topic.exam_date, date) else topic.exam_date.date()
        days_until_exam = (exam - today).days

    return TopicStats(
        total_cards=stats.total if stats else 0,
        due_cards=stats.due if stats else 0,
        new_cards=stats.new if stats else 0,
        learning_cards=stats.learning if stats else 0,
        review_cards=stats.review if stats else 0,
        relearning_cards=stats.relearning if stats else 0,
        days_until_exam=days_until_exam,
    )


def _to_response(api, topic, today: date) -> TopicResponse:
    stats = _topic_stats(api, topic, today)
    return TopicResponse.model_validate({**topic.model_dump(), "stats": stats})


def list_topics() -> list[TopicLean]:
    with db() as api:
        topics = api.list_topics()
    return [TopicLean.model_validate(t) for t in topics]


def list_topics_overview(today: date) -> list[TopicResponse]:
    with db() as api:
        topics = api.list_topics()
        return [_to_response(api, t, today) for t in topics]


def get_topic(topic_id: int, today: date) -> TopicResponse | None:
    with db() as api:
        t = api.get_topic(topic_id)
        if t is None:
            return None
        return _to_response(api, t, today)


def create_topic(data: TopicCreate, today: date) -> TopicResponse:
    db_data = DbTopicCreate.model_validate(data.model_dump())
    with db() as api:
        t = api.create_topic(db_data)
        return _to_response(api, t, today)


def update_topic(topic_id: int, data: TopicUpdate, today: date) -> TopicResponse | None:
    db_data = DbTopicUpdate.model_validate({"id": topic_id, **data.model_dump(exclude_unset=True)})
    with db() as api:
        t = api.update_topic(db_data)
        if t is None:
            return None
        return _to_response(api, t, today)


def delete_topic(topic_id: int) -> bool:
    with db() as api:
        images = [
            (c.front_image, c.back_image)
            for d in api.list_decks(topic_id=topic_id) or []
            for c in api.list_cards(deck_id=d.id) or []
        ]
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
        decks = api.list_decks(topic_id=topic_id)
    if decks is None:
        return None
    return [DeckLean.model_validate(d) for d in decks]
