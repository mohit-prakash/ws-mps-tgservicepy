import os
import uuid
import asyncio
from app.telegram_client.client import telethon_client, ensure_client_started
from app.config.settings import SAVE_BASE

TEMP_DOWNLOAD_DIR = os.path.join(SAVE_BASE, "downloads")

_download_progress = {}


def get_download_progress(download_id: str):
    return _download_progress.get(download_id)


async def _perform_download(download_id: str, chat_id: int, message_id: int):
    def progress_callback(current, total):
        if total > 0:
            _download_progress[download_id]["percent"] = int((current / total) * 100)
        else:
            _download_progress[download_id]["percent"] = 100 if current > 0 else 0

    try:
        await ensure_client_started()

        msg = await telethon_client.get_messages(chat_id, ids=message_id)
        if not msg or not msg.media:
            _download_progress[download_id].update({
                "status": "error",
                "error": "Message not found or has no media"
            })
            return

        # Extract filename
        filename = None
        if getattr(msg, "document", None):
            for attr in msg.document.attributes:
                if hasattr(attr, "file_name"):
                    filename = attr.file_name
                    break

        if not filename:
            filename = f"msg_{message_id}"

        os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
        target_path = os.path.join(TEMP_DOWNLOAD_DIR, f"{download_id}_{filename}")

        _download_progress[download_id].update({
            "status": "downloading",
            "percent": 0,
            "file_name": filename,
            "file_path": target_path
        })

        path = await telethon_client.download_media(
            msg,
            file=target_path,
            progress_callback=progress_callback
        )

        if path:
            _download_progress[download_id].update({
                "status": "completed",
                "percent": 100,
                "file_path": path
            })
        else:
            _download_progress[download_id].update({
                "status": "error",
                "error": "Download failed"
            })

    except Exception as e:
        _download_progress[download_id].update({
            "status": "error",
            "error": str(e)
        })


async def download_media(chat_id: int, message_id: int):
    """
    Downloads media to TEMP directory on server.
    Client will download via HTTP.
    """
    download_id = uuid.uuid4().hex[:10]

    _download_progress[download_id] = {
        "status": "pending",
        "percent": 0,
        "file_name": "determining_filename...",
        "file_path": None
    }

    asyncio.create_task(
        _perform_download(
            download_id=download_id,
            chat_id=chat_id,
            message_id=message_id
        )
    )

    return {
        "status": "started",
        "download_id": download_id
    }