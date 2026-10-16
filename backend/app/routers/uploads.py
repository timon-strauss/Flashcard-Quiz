from fastapi import APIRouter, UploadFile, File
from ..services.image_service import save_image

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("")
async def upload_image(file: UploadFile = File(...)):
    data = await file.read()
    filename = save_image(file, data)
    return {"filename": filename}
