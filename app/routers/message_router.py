from fastapi import APIRouter
from app.services.message_service import get_all_message_metadata, get_msg

router = APIRouter()

@router.get("/get_all_message_metadata")
async def get_message_ids(
    chat_id: int,
    after_message_id: int = None
):
    messages = await get_all_message_metadata(
        chat_id=chat_id,
        after_message_id=after_message_id
    )

    return {
        "chat_id": chat_id,
        "count": len(messages),
        "messages": messages
    }

@router.get("/get_message")
async def get_message(chat_id: int, message_id: int):
    message = await get_msg(chat_id, message_id)
    return {"chat_id": chat_id, "message": message}