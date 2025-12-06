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

async def get_all_message_ids(chat_id: int):
    """Iterates through all messages in a chat and returns a dictionary of message IDs to file names."""
    await ensure_client_started()
    message_files = {}
    async for msg in telethon_client.iter_messages(chat_id, limit=None):
        if msg.file and hasattr(msg.file, 'name'):
            message_files[msg.id] = msg.file.name
    return message_files

async def get_msg(chat_id: int, message_id: int):
    """Gets a specific message from a chat by its ID and returns it as a serializable dictionary."""
    await ensure_client_started()
    message = await telethon_client.get_messages(chat_id, ids=message_id)
    if message:
        message_dict = message.to_dict()
        return _make_serializable(message_dict)
    return None
