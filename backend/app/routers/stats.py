from fastapi import APIRouter, HTTPException, Query
from .schemas import DueDay, ProgressDay, ReviewDay
from ..services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/reviews", response_model=list[ReviewDay])
def review_history(
    days: int = Query(30, ge=1, le=365),
    deck_id: int | None = None,
    topic_id: int | None = None,
    tz_offset: int = Query(0, ge=-840, le=840, description="Minutes east of UTC"),
):
    """Reviews per day over the last `days` days, for everything, one topic or one deck."""
    history = stats_service.review_history(
        days, deck_id=deck_id, topic_id=topic_id, tz_offset_minutes=tz_offset
    )
    if history is None:
        raise HTTPException(status_code=404, detail="Deck oder Projekt nicht gefunden")
    return history


@router.get("/due", response_model=list[DueDay])
def due_forecast(
    days: int = Query(14, ge=1, le=365),
    deck_id: int | None = None,
    topic_id: int | None = None,
    tz_offset: int = Query(0, ge=-840, le=840, description="Minutes east of UTC"),
):
    """Cards becoming due per day over the next `days` days; overdue cards count towards today."""
    forecast = stats_service.due_forecast(
        days, deck_id=deck_id, topic_id=topic_id, tz_offset_minutes=tz_offset
    )
    if forecast is None:
        raise HTTPException(status_code=404, detail="Deck oder Projekt nicht gefunden")
    return forecast


@router.get("/progress", response_model=list[ProgressDay])
def progress_history(
    days: int = Query(30, ge=1, le=365),
    deck_id: int | None = None,
    topic_id: int | None = None,
    tz_offset: int = Query(0, ge=-840, le=840, description="Minutes east of UTC"),
):
    """Ready cards at the end of each day, from the first review on (at most `days` days)."""
    progress = stats_service.progress_history(
        days, deck_id=deck_id, topic_id=topic_id, tz_offset_minutes=tz_offset
    )
    if progress is None:
        raise HTTPException(status_code=404, detail="Deck oder Projekt nicht gefunden")
    return progress
