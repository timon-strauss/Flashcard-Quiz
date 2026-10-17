from datetime import date
from fastapi import APIRouter, HTTPException
from .schemas import TopicCreate, TopicUpdate, TopicLean, TopicResponse, DeckLean
from ..services import topic_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicLean])
def list_topics():
    return topic_service.list_topics()


@router.get("/overview", response_model=list[TopicResponse])
def list_topics_overview():
    return topic_service.list_topics_overview(date.today())


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int):
    topic = topic_service.get_topic(topic_id, date.today())
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("", response_model=TopicResponse, status_code=201)
def create_topic(body: TopicCreate):
    return topic_service.create_topic(body, date.today())


@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(topic_id: int, body: TopicUpdate):
    topic = topic_service.update_topic(topic_id, body, date.today())
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: int):
    if not topic_service.delete_topic(topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")


@router.get("/{topic_id}/decks", response_model=list[DeckLean])
def list_topic_decks(topic_id: int):
    decks = topic_service.list_topic_decks(topic_id)
    if decks is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return decks
