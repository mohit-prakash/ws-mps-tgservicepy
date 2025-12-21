import base64
from datetime import datetime
from app.telegram_client.client import telethon_client, ensure_client_started
from typing import List, Dict, Optional
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
from telethon.tl.types import PhotoSize, PhotoCachedSize

logger = logging.getLogger(__name__)

def _make_serializable(data):
    """Recursively converts non-serializable data types in a dictionary or list."""
    if isinstance(data, dict):
        return {key: _make_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_make_serializable(item) for item in data]
    elif isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    elif isinstance(data, datetime):
        return data.isoformat()
    return data

def extract_duration(msg) -> Optional[float]:
    if not msg or not msg.media:
        return None

    document = getattr(msg.media, "document", None)
    if not document or not document.attributes:
        return None

    for attr in document.attributes:
        if attr.__class__.__name__ == "DocumentAttributeVideo":
            return attr.duration

    return None


def extract_width_height(msg):
    if not msg or not msg.media:
        return None, None

    document = getattr(msg.media, "document", None)
    if not document or not document.attributes:
        return None, None

    for attr in document.attributes:
        if attr.__class__.__name__ in (
            "DocumentAttributeVideo",
            "DocumentAttributeImageSize",
        ):
            return attr.w, attr.h

    return None, None

def extract_message_metadata(msg, chat_id: int):
    if not msg or not msg.media or not msg.file:
        return None

    mime_type = msg.file.mime_type
    if not mime_type:
        return None

    if mime_type.startswith("image/"):
        media_type = "Photo"
    elif mime_type.startswith("video/"):
        media_type = "Video"
    else:
        return None

    width, height = extract_width_height(msg)
    duration = extract_duration(msg) if media_type == "Video" else None

    return {
        "chat_id": chat_id,
        "message_id": msg.id,
        "message_type": media_type,
        "media_type": media_type,
        "caption": msg.text or None,
        "message_date": msg.date.isoformat() if msg.date else None,
        "file_name": msg.file.name,
        "mime_type": mime_type,
        "file_size": msg.file.size,
        "duration": duration,
        "width": width,
        "height": height,
    }

async def get_all_message_metadata(
    chat_id: int,
    after_message_id: Optional[int] = None,
):
    await ensure_client_started()

    results = []

    async for msg in telethon_client.iter_messages(chat_id):
        try:
            if after_message_id and msg.id <= after_message_id:
                break

            metadata = extract_message_metadata(msg, chat_id)
            if metadata:
                results.append(metadata)

        except Exception as e:
            logger.error(
                f"Failed to process message_id={msg.id} chat_id={chat_id}: {e}",
                exc_info=True
            )

    return results

async def get_msg_metadata(
    chat_id: int,
    message_id: int,
) -> Optional[dict]:
    await ensure_client_started()

    try:
        msg = await telethon_client.get_messages(
            entity=chat_id,
            ids=message_id
        )

        if not msg:
            return None

        return extract_message_metadata(msg, chat_id)

    except Exception as e:
        logger.error(
            f"Failed to fetch message metadata "
            f"chat_id={chat_id} message_id={message_id}: {e}",
            exc_info=True
        )
        return None

async def get_msg(chat_id: int, message_id: int):
    """Gets a specific message from a chat by its ID and returns it as a serializable dictionary."""
    await ensure_client_started()
    message = await telethon_client.get_messages(chat_id, ids=message_id)
    if message:
        message_dict = message.to_dict()
        return _make_serializable(message_dict)
    return None
