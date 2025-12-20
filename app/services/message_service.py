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


async def get_all_message_metadata(
    chat_id: int,
    after_message_id: Optional[int] = None,
) -> List[Dict]:
    """
    Fetch message metadata for all media messages in a chat.

    If after_message_id is provided, only messages with id > after_message_id
    are returned. Otherwise, all messages are processed.
    """
    await ensure_client_started()

    results: List[Dict] = []

    async for msg in telethon_client.iter_messages(chat_id):
        try:
            # Skip older messages if after_message_id is provided
            if after_message_id and msg.id <= after_message_id:
                break

            if not msg.media or not msg.file:
                continue

            mime_type = msg.file.mime_type
            file_name = msg.file.name
            file_size = msg.file.size

            if not mime_type:
                continue

            # Detect media type
            if mime_type.startswith("image/"):
                media_type = "Photo"
            elif mime_type.startswith("video/"):
                media_type = "Video"
            else:
                continue

            # Extract optional fields
            width, height = extract_width_height(msg)
            duration = extract_duration(msg) if media_type == "Video" else None

            results.append({
                "chat_id": chat_id,
                "message_id": msg.id,
                "message_type": media_type,
                "media_type": media_type,
                "caption": msg.text or None,
                "message_date": msg.date.isoformat() if msg.date else None,
                "file_name": file_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "duration": duration,
                "width": width,
                "height": height,
            })

        except Exception as e:
            # IMPORTANT: never crash batch processing
            logger.error(
                f"Failed to process message_id={msg.id} chat_id={chat_id}: {e}",
                exc_info=True
            )

    return results

async def get_msg(chat_id: int, message_id: int):
    """Gets a specific message from a chat by its ID and returns it as a serializable dictionary."""
    await ensure_client_started()
    message = await telethon_client.get_messages(chat_id, ids=message_id)
    if message:
        message_dict = message.to_dict()
        return _make_serializable(message_dict)
    return None
