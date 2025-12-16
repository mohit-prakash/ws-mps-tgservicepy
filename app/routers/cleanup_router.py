from fastapi import APIRouter, Query, HTTPException
from app.services.cleanup_service import cleanup_directory

router = APIRouter(prefix="/cleanup", tags=["Cleanup"])

@router.delete("")
async def cleanup_files(
    path: str = Query(..., description="upload | download | thumb")
):
    result = cleanup_directory(path)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result