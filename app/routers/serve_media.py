from fastapi import APIRouter, HTTPException, Request, Query, status
from fastapi.responses import (
    StreamingResponse,
    FileResponse,
    JSONResponse
)
import os
import mimetypes

from app.services.download_service import get_download_progress

router = APIRouter()


@router.get("/media")
async def serve_media(
    request: Request,
    download_id: str = Query(..., description="Download ID"),
    mode: str = Query("stream", enum=["stream", "download"])
):
    """
    mode=stream   → inline playback (video/audio)
    mode=download → force file download
    """

    progress = get_download_progress(download_id)

    # ❌ Invalid ID
    if not progress:
        raise HTTPException(status_code=404, detail="Invalid download ID")

    # ⏳ Still downloading → HTTP 202 Accepted
    if progress["status"] != "completed":
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": progress["status"],
                "percent": progress.get("percent", 0),
                "file_name": progress.get("file_name")
            }
        )

    file_path = progress.get("file_path")
    file_name = progress.get("file_name")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(file_name)
    media_type = mime_type or "application/octet-stream"

    # Decide stream vs download
    disposition = "inline" if mode == "stream" else "attachment"
    content_disposition = f'{disposition}; filename="{file_name}"'

    # ▶️ No Range header → normal response
    if not range_header:
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={
                "Content-Disposition": content_disposition,
                "Accept-Ranges": "bytes"
            }
        )

    # 🔁 Parse Range header
    range_value = range_header.replace("bytes=", "")
    start_str, end_str = range_value.split("-")

    start = int(start_str)
    end = int(end_str) if end_str else file_size - 1
    end = min(end, file_size - 1)

    if start >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    content_length = end - start + 1

    # 🔹 Range generator (1MB chunks)
    def range_generator():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = f.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Disposition": content_disposition
    }

    return StreamingResponse(
        range_generator(),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        media_type=media_type,
        headers=headers
    )