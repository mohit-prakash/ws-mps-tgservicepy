import base64
from datetime import datetime
from app.telegram_client.client import telethon_client, ensure_client_started

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

async def get_all_message_metadata(
    chat_id: int,
    after_message_id: int | None = None
):
    await ensure_client_started()

    messages = []

    async for msg in telethon_client.iter_messages(
        chat_id,
        min_id=after_message_id,
        reverse=True
    ):
        if not msg.file:
            continue

        mime_type = msg.file.mime_type or ""
        file_name = msg.file.name
        file_size = msg.file.size

        # Determine media type
        if mime_type.startswith("image/"):
            media_type = "Photo"
        elif mime_type.startswith("video/"):
            media_type = "Video"
        else:
            media_type = "File"

        width = height = duration = None

        # 1️⃣ Primary extraction (fast path)
        if msg.photo and msg.photo.sizes:
            largest = msg.photo.sizes[-1]
            width = largest.w
            height = largest.h

        if msg.video:
            duration = msg.video.duration
            width = msg.video.w
            height = msg.video.h

        # 2️⃣ Fallback to document attributes (your requirement)
        if (width is None or height is None or duration is None) and msg.media:
            doc = getattr(msg.media, "document", None)
            doc_w, doc_h, doc_dur = _extract_doc_attributes(doc)

            width = width or doc_w
            height = height or doc_h
            duration = duration or doc_dur

        messages.append({
            "chat_id": chat_id,
            "message_id": msg.id,
            "message_type": media_type,
            "caption": msg.text,
            "message_date": msg.date.isoformat() if msg.date else None,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_size": file_size,
            "media_type": media_type,
            "duration": duration,
            "width": width,
            "height": height
        })

    return messages

def _extract_doc_attributes(document):
    width = height = duration = None

    if not document or not document.attributes:
        return width, height, duration

    for attr in document.attributes:
        attr_type = attr.__class__.__name__

        if attr_type == "DocumentAttributeImageSize":
            width = attr.w
            height = attr.h

        elif attr_type == "DocumentAttributeVideo":
            duration = attr.duration
            # width/height may also exist here
            width = width or attr.w
            height = height or attr.h

    return width, height, duration

async def get_msg(chat_id: int, message_id: int):
    """Gets a specific message from a chat by its ID and returns it as a serializable dictionary."""
    await ensure_client_started()
    message = await telethon_client.get_messages(chat_id, ids=message_id)
    if message:
        message_dict = message.to_dict()
        return _make_serializable(message_dict)
    return None
