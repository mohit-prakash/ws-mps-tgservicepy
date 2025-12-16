from fastapi import APIRouter, Form, Query
from app.services.search_service import search_messages_by_file_or_caption

search_router = APIRouter()


@search_router.post("/search")
async def search_by_file(
    chat_id: int = Form(..., description="Telegram chat ID"),
    limit: int = Form(-1, description="Number of messages to search (-1 for entire chat)"),
    file_name: str = Query(None, description="File name to search"),
    caption: str = Query(None, description="Caption text to search")
):
    """
    Search Telegram messages by file name and/or caption.
    Returns only message IDs.
    """

    if not file_name and not caption:
        return {
            "status": "error",
            "error": "Provide file_name or caption"
        }

    search_limit = None if limit == -1 else limit

    try:
        message_ids = await search_messages_by_file_or_caption(
            chat_id=chat_id,
            file_name=file_name,
            caption=caption,
            limit=search_limit
        )

        return {
            "status": "success",
            "count": len(message_ids),
            "message_ids": message_ids
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }