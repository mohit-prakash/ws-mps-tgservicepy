import os
import uuid
import asyncio
from telethon.errors import (
    FloodWaitError,
    RPCError
)
# Python built-in connection error
from asyncio import TimeoutError
from aiohttp import ClientConnectionError
from app.telegram_client.client import telethon_client, ensure_client_started

# In-memory upload tracker
_upload_progress = {}

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def get_upload_progress(upload_id: str):
    return _upload_progress.get(upload_id)


async def _perform_upload(upload_id: str, chat_id: int, file_path: str, caption: str, thumb: str, cleanup_paths: list = None):
    def progress_callback(current, total):
        percent = int((current / total) * 100)
        _upload_progress[upload_id]["percent"] = percent

    try:
        await ensure_client_started()

        # Validate files
        if not os.path.exists(file_path):
            _upload_progress[upload_id]["status"] = "error"
            _upload_progress[upload_id]["error"] = "File not found"
            return

        if thumb and not os.path.exists(thumb):
            _upload_progress[upload_id]["status"] = "error"
            _upload_progress[upload_id]["error"] = "Thumbnail not found"
            return

        retries = 0

        while retries <= MAX_RETRIES:

            try:
                # Attempt upload
                result = await telethon_client.send_file(
                    chat_id,
                    file_path,
                    caption=caption,
                    thumb=thumb,
                    supports_streaming=True,
                    progress_callback=progress_callback
                )

                # SUCCESS
                msg = result[0] if isinstance(result, (list, tuple)) else result
                message_id = getattr(msg, "id", None)

                _upload_progress[upload_id]["status"] = "completed"
                _upload_progress[upload_id]["percent"] = 100
                _upload_progress[upload_id]["message_id"] = message_id
                return

            except FloodWaitError as fw:
                # Telegram rate-limit error
                wait_time = fw.seconds
                _upload_progress[upload_id]["status"] = "retrying"
                _upload_progress[upload_id]["error"] = f"FloodWait: waiting {wait_time}s"

                await asyncio.sleep(wait_time)
                retries += 1


            except (ClientConnectionError, TimeoutError, RPCError) as e:
                # Retryable network errors
                if retries < MAX_RETRIES:
                    _upload_progress[upload_id]["status"] = "retrying"
                    _upload_progress[upload_id]["error"] = f"Retry {retries + 1}/{MAX_RETRIES}"

                    await asyncio.sleep(RETRY_DELAY)
                    retries += 1
                    continue
                else:
                    raise e

            except Exception as e:
                # Non-retryable or last retry failed
                raise e

        # If reached here: failed after all retries
        _upload_progress[upload_id]["status"] = "error"
        _upload_progress[upload_id]["error"] = f"Upload failed after {MAX_RETRIES} retries"

    except Exception as e:
        _upload_progress[upload_id]["status"] = "error"
        _upload_progress[upload_id]["error"] = str(e)
    finally:
        if cleanup_paths:
            for path in cleanup_paths:
                if path and os.path.exists(path):
                    os.remove(path)


async def upload_using_file_path(chat_id: int, file_path: str, caption: str = None, thumb: str = None, cleanup_paths: list = None, upload_id: str = None):
    # upload_id = uuid.uuid4().hex[:10]
    file_name = os.path.basename(file_path)

    _upload_progress[upload_id] = {
        "status": "uploading",
        "percent": 0,
        "message_id": None,
        "file_name": file_name
    }

    asyncio.create_task(
        _perform_upload(
            upload_id=upload_id,
            chat_id=chat_id,
            file_path=file_path,
            caption=caption,
            thumb=thumb,
            cleanup_paths=cleanup_paths
        )
    )

    return {
        "status": "started",
        "upload_id": upload_id,
        "file_name": file_name
    }
