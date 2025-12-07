import os
import uuid
import asyncio
from app.telegram_client.client import telethon_client, ensure_client_started
from app.config.settings import SAVE_BASE

# In-memory download tracker
_download_progress = {}

def get_download_progress(download_id: str):
    """Retrieves the current progress for a given download ID."""
    # The _download_progress dictionary already stores 'file_path'
    # when the download is completed, so simply returning the entry
    # will include it if available.
    return _download_progress.get(download_id)

async def _perform_download(download_id: str, chat_id: int, message_id: int):
    """
    Performs the actual media download in a background task,
    updating the progress tracker.
    """
    def progress_callback(current, total):
        if total > 0:
            percent = int((current / total) * 100)
            _download_progress[download_id]["percent"] = percent
        else:
            # Handle cases where total is 0 (e.g., very small files, or metadata only)
            _download_progress[download_id]["percent"] = 100 if current > 0 else 0

    try:
        await ensure_client_started()

        # Fetch message to get media and filename
        msg = await telethon_client.get_messages(chat_id, ids=message_id)
        if not msg or not msg.media:
            _download_progress[download_id]["status"] = "error"
            _download_progress[download_id]["error"] = "Message not found or has no media"
            return

        # Determine filename
        filename = None
        try:
            if getattr(msg, 'document', None):
                for attr in msg.document.attributes:
                    if hasattr(attr, 'file_name'):
                        filename = attr.file_name
                        break
        except Exception:
            pass # filename remains None

        if not filename:
            filename = f"msg_{message_id}"

        downloads_dir = os.path.join(SAVE_BASE, 'files')
        os.makedirs(downloads_dir, exist_ok=True)
        target_file_path = os.path.join(downloads_dir, filename)

        # Update progress with actual filename and status
        _download_progress[download_id]["file_name"] = filename
        _download_progress[download_id]["status"] = "downloading"
        _download_progress[download_id]["percent"] = 0

        # Perform the actual download
        path = await telethon_client.download_media(msg, file=target_file_path, progress_callback=progress_callback)

        if path:
            _download_progress[download_id]["status"] = "completed"
            _download_progress[download_id]["percent"] = 100
            _download_progress[download_id]["file_path"] = path # Store the final path
        else:
            _download_progress[download_id]["status"] = "error"
            _download_progress[download_id]["error"] = "Download failed or returned no path"

    except Exception as e:
        _download_progress[download_id]["status"] = "error"
        _download_progress[download_id]["error"] = str(e)


async def download_media(chat_id: int, message_id: int) -> dict:
    """
    Initiates a media download as a background task and returns a download ID.
    """
    download_id = uuid.uuid4().hex[:10]

    # Initialize progress with a placeholder filename
    _download_progress[download_id] = {
        "status": "pending",
        "percent": 0,
        "file_name": "determining_filename...", # Placeholder until actual filename is known
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