from fastapi import FastAPI, HTTPException
import os
from app.config.settings import API_ID, API_HASH, SESSION_PATH, SAVE_BASE
from app.telegram_client.client import telethon_client, ensure_client_started
from app.services.thumb_service import download_thumbnail
from app.routers import upload_router, message_router, download_router, delete_router,search_router, serve_media, cleanup_router

app = FastAPI(title="telegram-python-service")
app.include_router(upload_router.router, prefix="/api")
app.include_router(message_router.router, prefix="/api")
app.include_router(download_router.router, prefix="/api")
app.include_router(delete_router.router, prefix="/api")
app.include_router(search_router.search_router, prefix="/api")
app.include_router(serve_media.router, prefix="/api")
app.include_router(cleanup_router.router, prefix="/api")

# Create base folders
os.makedirs(SAVE_BASE, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    # Ensure Telethon client started
    await ensure_client_started()

@app.on_event("shutdown")
async def shutdown_event():
    await telethon_client.disconnect()


@app.get("/thumbnail")
async def thumbnail(chat_id: int, msg_id: int):
    try:
        # download_thumbnail already returns {"status": "...", "path": "..."}
        result = await download_thumbnail(chat_id, msg_id)
        if result["status"] == "fail":
            raise HTTPException(status_code=404, detail="Thumbnail not available")
        return result # Directly return the result
    except HTTPException:
        raise # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
