from fastapi import APIRouter
from .schemas import TopicCreate, TopicUpdate, TopicLean, TopicResponse, DeckLean, _not_implemented

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicLean])
def list_topics():
    _not_implemented()


@router.get("/overview", response_model=list[TopicResponse])
def list_topics_overview():
    _not_implemented()


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int):
    _not_implemented()


@router.post("", response_model=TopicResponse)
def create_topic(body: TopicCreate):
    _not_implemented()


@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(topic_id: int, body: TopicUpdate):
    _not_implemented()


@router.delete("/{topic_id}")
def delete_topic(topic_id: int):
    _not_implemented()


@router.get("/{topic_id}/decks", response_model=list[DeckLean])
def list_topic_decks(topic_id: int):
    _not_implemented()
