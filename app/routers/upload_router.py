from fastapi import APIRouter, UploadFile, File, Form
import os
import uuid
from app.services.upload_service import upload_using_file_path

router = APIRouter()

UPLOAD_TEMP_DIR = "temp_uploads"
os.makedirs(UPLOAD_TEMP_DIR, exist_ok=True)


@router.post("/upload_using_file")
async def upload_using_file(
    file: UploadFile = File(...),
    thumb: UploadFile = File(None),
    caption: str = Form(None),
    chat_id: int = Form(...)
):
    # save file temporarily
    temp_name = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(UPLOAD_TEMP_DIR, temp_name)

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    thumb_path = None
    if thumb:
        # Save thumb temporarily
        thumb_temp_name = f"{uuid.uuid4()}_{thumb.filename}"
        thumb_path = os.path.join(UPLOAD_TEMP_DIR, thumb_temp_name)
        with open(thumb_path, "wb") as f:
            f.write(await thumb.read())

    try:
        # Upload to Telegram
        result = await upload_using_file_path(chat_id, temp_path, caption, thumb=thumb_path)
    finally:
        # Cleanup
        os.remove(temp_path)
        if thumb_path:
            os.remove(thumb_path)

    return result

@router.post("/upload_using_path")
async def upload_using_path(path: str = Form(...), thumb: str = Form(None), caption: str = Form(None), chat_id: int = Form(...)):
    # Validate file exists
    if not os.path.isfile(path):
        return {"error": "File not found", "path": path}

    # Direct upload to Telegram
    return await upload_using_file_path(chat_id, path, caption, thumb=thumb)