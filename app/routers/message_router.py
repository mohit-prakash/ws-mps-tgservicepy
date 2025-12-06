from fastapi import APIRouter
from app.services.message_service import get_all_message_ids, get_msg

router = APIRouter()

@router.get("/get_message_ids")
async def get_message_ids(chat_id: int):
    message_files = await get_all_message_ids(chat_id)
    return {"chat_id": chat_id, "message_files": message_files}

@router.get("/get_message")
async def get_message(chat_id: int, message_id: int):
    message = await get_msg(chat_id, message_id)
    return {"chat_id": chat_id, "message": message}