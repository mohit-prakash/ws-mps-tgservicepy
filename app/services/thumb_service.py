import os
from app.telegram_client.client import telethon_client, ensure_client_started
from app.config.settings import SAVE_BASE

async def download_thumbnail(chat_id: int, message_id: int) -> str:
    """Download only the best thumbnail for a message. Returns absolute path or None."""
    await ensure_client_started()

    msg = await telethon_client.get_messages(chat_id, ids=message_id)
    if not msg or not msg.media:
        return None

    thumbs_dir = os.path.join(SAVE_BASE, 'thumbs')
    os.makedirs(thumbs_dir, exist_ok=True)

    # Telethon supports downloading thumbnail via thumb=True
    target = os.path.join(thumbs_dir, f"thumb_{message_id}.jpg")
    # Use telethon_client.download_media with thumb=True
    path = await telethon_client.download_media(msg, file=target, thumb=True)
    # telethon may return None for thumb downloads but file will be at target
    return path or target