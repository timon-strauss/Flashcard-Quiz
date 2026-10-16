import uuid
import os
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Upload")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}


def save_image(file: UploadFile, data: bytes) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid.uuid4()}{ext}"

    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(data)

    return filename


def delete_image(filename: str) -> bool:
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True
