from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
from app.config.settings import API_ID, API_HASH, SESSION_PATH, SAVE_BASE
from app.telegram_client.client import telethon_client, ensure_client_started
from app.services.thumb_service import download_thumbnail
from app.services.download_service import download_media
from app.routers import upload_router, message_router

app = FastAPI(title="telegram-python-service")
app.include_router(upload_router.router, prefix="/api")
app.include_router(message_router.router, prefix="/api")

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
        path = await download_thumbnail(chat_id, msg_id)
        if not path:
            raise HTTPException(status_code=404, detail="Thumbnail not available")
        return {"thumbnail_path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download")
async def download(chat_id: int, msg_id: int):
    try:
        path = await download_media(chat_id, msg_id)
        if not path:
            raise HTTPException(status_code=404, detail="Media not available")
        return {"file_path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))