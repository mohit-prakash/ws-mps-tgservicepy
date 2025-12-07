from fastapi import APIRouter, HTTPException
from app.services.delete_service import delete_file

router = APIRouter()

@router.delete("/delete", response_model=dict)
async def delete_media_route(chat_id: int, message_id: int, revoke: bool = False):
    """
    API endpoint to delete a message from a Telegram chat.
    """
    result = await delete_file(chat_id=chat_id, message_id=message_id, revoke=revoke)
    if result["status"] == "fail":
        raise HTTPException(status_code=500, detail=result["message"])
    return result
