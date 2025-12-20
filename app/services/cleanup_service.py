import os
import shutil
from app.config.settings import SAVE_BASE

ALLOWED_PATHS = {
    "upload": "uploads",
    "download": "downloads",
    "thumb": "thumbs"
}

def cleanup_directory(path_key: str) -> dict:
    """
    Deletes all files inside allowed SAVE_BASE subdirectories.
    If path_key is 'upload' or 'download' it also clears the corresponding
    in-memory progress dictionary from the upload/download services.
    """

    if path_key not in ALLOWED_PATHS:
        return {
            "status": "error",
            "error": "Invalid path. Use `upload`, `download`, or `thumb`"
        }

    target_dir = os.path.join(SAVE_BASE, ALLOWED_PATHS[path_key])

    if not os.path.exists(target_dir):
        # still attempt to clear progress dicts even if directory missing
        cleared = _clear_progress_if_needed(path_key)
        return {
            "status": "success",
            "message": f"{path_key} directory does not exist. Nothing to clean.",
            **cleared
        }

    deleted_files = 0
    deleted_dirs = 0

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                deleted_files += 1
            except Exception:
                pass

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
                deleted_dirs += 1
            except Exception:
                pass

    cleared = _clear_progress_if_needed(path_key)

    return {
        "status": "success",
        "cleaned": path_key,
        "deleted_files": deleted_files,
        "deleted_dirs": deleted_dirs,
        **cleared
    }

def _clear_progress_if_needed(path_key: str) -> dict:
    """
    Lazily import upload/download progress dicts and remove only entries
    whose 'status' is 'error' or 'completed'. Returns info about how many
    entries were cleared or any import/processing error.
    """
    result = {}
    terminal_statuses = {"error", "completed"}

    try:
        if path_key == "upload":
            from app.services.upload_service import _upload_progress as _up
            removed = 0
            for k in list(_up.keys()):
                entry = _up.get(k)
                if entry and entry.get("status") in terminal_statuses:
                    _up.pop(k, None)
                    removed += 1
            result["cleared_upload_progress"] = removed

        if path_key == "download":
            from app.services.download_service import _download_progress as _dp
            removed = 0
            for k in list(_dp.keys()):
                entry = _dp.get(k)
                if entry and entry.get("status") in terminal_statuses:
                    _dp.pop(k, None)
                    removed += 1
            result["cleared_download_progress"] = removed

    except Exception as e:
        result["progress_clear_error"] = str(e)

    return result
