import os
import sys
from app.telegram_client.client import telethon_client, ensure_client_started

async def upload_using_file_path(chat_id: int, file_path: str, caption: str = None, thumb: str = None):
    """Upload a file to a target chat_id (username or id). Returns sent message."""
    await ensure_client_started()
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    if thumb and not os.path.exists(thumb):
        raise FileNotFoundError(f"Thumbnail file not found: {thumb}")


    result = await telethon_client.send_file(chat_id, file_path, caption=caption, thumb=thumb, supports_streaming=True)
    # Normalize result (Telethon may return a single Message or a list)
    msg = result[0] if isinstance(result, (list, tuple)) else result
    message_id = getattr(msg, "id", None)

    return {
        "status": "uploaded",
        "file_name": os.path.basename(file_path),
        "message_id": message_id
    }
