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
    """

    if path_key not in ALLOWED_PATHS:
        return {
            "status": "error",
            "error": "Invalid path. Use 'upload', 'download', or 'thumb'"
        }

    target_dir = os.path.join(SAVE_BASE, ALLOWED_PATHS[path_key])

    if not os.path.exists(target_dir):
        return {
            "status": "success",
            "message": f"{path_key} directory does not exist. Nothing to clean."
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

    return {
        "status": "success",
        "cleaned": path_key,
        "deleted_files": deleted_files,
        "deleted_dirs": deleted_dirs
    }