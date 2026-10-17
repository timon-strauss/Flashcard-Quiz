import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ..services import transfer_service

router = APIRouter(tags=["transfer"])


@router.get("/export/deck/{deck_id}")
def export_deck(deck_id: int):
    data = transfer_service.export_deck(deck_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    filename = f"deck_{deck_id}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/topic/{topic_id}")
def export_topic(topic_id: int):
    data = transfer_service.export_topic(topic_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    filename = f"topic_{topic_id}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_transfer(
    file: UploadFile = File(...),
    target_topic_id: int | None = Form(None),
):
    if file.content_type not in ("application/json", "text/plain", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    raw = await file.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    try:
        result = transfer_service.import_transfer(payload, target_topic_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result
