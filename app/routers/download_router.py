from fastapi import APIRouter, Form, HTTPException
from app.services.download_service import download_media, get_download_progress

router = APIRouter()

@router.post("/download")
async def initiate_download(
    chat_id: int = Form(...),
    message_id: int = Form(...)
):
    """
    Initiates a media download from Telegram and returns a download ID.
    """
    response = await download_media(chat_id=chat_id, message_id=message_id)
    return response

@router.get("/download_progress")
async def get_progress(download_id: str):
    """
    Retrieves the current progress of a specific download.
    """
    progress = get_download_progress(download_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Download ID not found")
    return progress
