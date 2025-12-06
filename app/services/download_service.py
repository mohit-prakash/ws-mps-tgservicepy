import os
from app.telegram_client.client import telethon_client, ensure_client_started
from app.config.settings import SAVE_BASE

async def download_media(chat_id: int, message_id: int) -> str:
    """Download the main media for a message. Returns absolute path or None."""
    await ensure_client_started()

    msg = await telethon_client.get_messages(chat_id, ids=message_id)
    if not msg or not msg.media:
        return None

    downloads_dir = os.path.join(SAVE_BASE, 'files')
    os.makedirs(downloads_dir, exist_ok=True)

    # Choose a friendly filename: msg_<id> or original file name
    filename = None
    try:
        # Try to read document attributes for original filename
        if getattr(msg, 'document', None):
            for attr in msg.document.attributes:
                if hasattr(attr, 'file_name'):
                    filename = attr.file_name
                    break
    except Exception:
        filename = None

    if not filename:
        filename = f"msg_{message_id}"

    target = os.path.join(downloads_dir, filename)
    path = await telethon_client.download_media(msg, file=target)
    return path or target