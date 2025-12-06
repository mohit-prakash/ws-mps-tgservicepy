import asyncio
from telethon import TelegramClient
from app.config.settings import API_ID, API_HASH, SESSION_PATH

# Create single Telethon client instance. Use session path WITHOUT .session suffix
telethon_client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

_client_started = False
_client_lock = asyncio.Lock()

async def ensure_client_started():
    global _client_started
    async with _client_lock:
        if not _client_started:
            await telethon_client.connect()
            if not await telethon_client.is_user_authorized():
                # If session exists and is valid this should be True. If not, raise.
                raise RuntimeError('Telethon session not authorized. Ensure session file exists and is valid.')
            _client_started = True