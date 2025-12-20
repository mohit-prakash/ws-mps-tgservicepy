import os
import asyncio
from fastapi import UploadFile
from telethon.errors import (
    FloodWaitError,
    RPCError
)
from app.config.settings import SAVE_BASE
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

        # Detect image and size; if image >10MB, send as document (Telegram limitation)
        file_size = os.path.getsize(file_path)
        is_image = False
        try:
            from PIL import Image
            try:
                Image.open(file_path).verify()
                is_image = True
            except Exception:
                is_image = False
        except Exception:
            import imghdr
            is_image = imghdr.what(file_path) is not None

        force_document = False
        if is_image and file_size > 10 * 1024 * 1024:
            force_document = True

        send_thumb = None if force_document else thumb

        retries = 0

        while retries <= MAX_RETRIES:
            try:
                # Attempt upload; for large images send as document
                result = await telethon_client.send_file(
                    chat_id,
                    file_path,
                    caption=caption,
                    thumb=send_thumb,
                    force_document=force_document,
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
                wait_time = fw.seconds
                _upload_progress[upload_id]["status"] = "retrying"
                _upload_progress[upload_id]["error"] = f"FloodWait: waiting {wait_time}s"
                await asyncio.sleep(wait_time)
                retries += 1

            except (ClientConnectionError, TimeoutError, RPCError) as e:
                if retries < MAX_RETRIES:
                    _upload_progress[upload_id]["status"] = "retrying"
                    _upload_progress[upload_id]["error"] = f"Retry {retries + 1}/{MAX_RETRIES}"
                    await asyncio.sleep(RETRY_DELAY)
                    retries += 1
                    continue
                else:
                    raise e

            except Exception as e:
                raise e

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


async def upload_file_stream(chat_id: int, file: UploadFile, caption: str = None):
    import uuid, os, asyncio

    upload_id = uuid.uuid4().hex[:10]
    original_name = os.path.basename(file.filename)

    _upload_progress[upload_id] = {
        "status": "uploading",
        "percent": 0,
        "message_id": None,
        "file_name": original_name
    }

    uploads_dir = os.path.join(SAVE_BASE, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    temp_path = os.path.join(uploads_dir, f"{upload_id}_{original_name}")

    try:
        # Stream upload to disk (chunked)
        with open(temp_path, "wb") as f:
            while True:
                chunk = await file.read(4 * 1024 * 1024)  # 4MB
                if not chunk:
                    break
                f.write(chunk)

    except Exception as e:
        _upload_progress[upload_id]["status"] = "error"
        _upload_progress[upload_id]["error"] = str(e)
        return {
            "status": "error",
            "upload_id": upload_id,
            "file_name": original_name
        }

    asyncio.create_task(
        _perform_upload(
            upload_id=upload_id,
            chat_id=chat_id,
            file_path=temp_path,
            caption=caption,
            thumb=None,
            cleanup_paths=[temp_path]  # ✅ easy cleanup
        )
    )

    return {
        "status": "started",
        "upload_id": upload_id,
        "file_name": original_name
    }
