from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import uuid
from app.services.upload_service import upload_using_file_path, get_upload_progress

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
    upload_id = uuid.uuid4().hex[:10]
    temp_name = f"{upload_id}_{file.filename}"
    temp_path = os.path.join(UPLOAD_TEMP_DIR, temp_name)
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    thumb_path = None
    if thumb and thumb.filename:
        thumb_temp_name = f"{uuid.uuid4()}_{thumb.filename}"
        thumb_path = os.path.join(UPLOAD_TEMP_DIR, thumb_temp_name)
        with open(thumb_path, "wb") as f:
            f.write(await thumb.read())

    cleanup_paths = [temp_path]
    if thumb_path:
        cleanup_paths.append(thumb_path)

    response = await upload_using_file_path(
        chat_id=chat_id,
        file_path=temp_path,
        caption=caption,
        thumb=thumb_path,
        cleanup_paths=cleanup_paths,
        upload_id=upload_id
    )
    return response

@router.post("/upload_using_path")
async def upload_using_path(
    path: str = Form(...),
    thumb: str = Form(None),
    caption: str = Form(None),
    chat_id: int = Form(...)
):
    if not os.path.isfile(path):
        return {"error": "File not found", "path": path}

    upload_id = uuid.uuid4().hex[:10]
    response = await upload_using_file_path(chat_id, path, caption, thumb=thumb, upload_id=upload_id)
    return response


@router.get("/upload_progress")
async def get_progress(upload_id: str):
    progress = get_upload_progress(upload_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Upload ID not found")
    return progress