from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.upload_service import get_upload_progress, upload_file_stream

router = APIRouter()

@router.get("/upload_progress")
async def get_progress(upload_id: str):
    progress = get_upload_progress(upload_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Upload ID not found")
    return progress

@router.post("/upload_stream")
async def upload_stream(
    chat_id: int = Form(...),
    caption: str = Form(None),
    file: UploadFile = File(...)
):
    result = await upload_file_stream(
        chat_id=chat_id,
        file=file,
        caption=caption
    )
    return result