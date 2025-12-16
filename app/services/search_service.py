import base64
from datetime import datetime
from app.telegram_client.client import telethon_client, ensure_client_started


async def search_messages_by_file_or_caption(
    chat_id: int,
    file_name: str = None,
    caption: str = None,
    limit: int = None
):
    """
    Search messages by file name and/or caption.
    Returns only matching message IDs.
    limit=None → search entire chat history.
    """

    if not file_name and not caption:
        return []

    await ensure_client_started()

    message_ids = []

    async for msg in telethon_client.iter_messages(chat_id, limit=limit):
        msg_caption = msg.message or ""
        doc_name = getattr(msg.file, "name", None)

        file_match = (
            file_name.lower() in doc_name.lower()
            if file_name and doc_name
            else not file_name
        )

        caption_match = (
            caption.lower() in msg_caption.lower()
            if caption
            else True
        )

        if file_match and caption_match:
            message_ids.append(msg.id)

    return message_ids