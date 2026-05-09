import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from storage.session_store import session_exists, get_session_path
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["upload"])

@router.post("/{session_id}/upload")
async def upload_video(session_id: str, file: UploadFile = File(...)):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    dest = os.path.join(session_path, "video.mp4")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": "video.mp4", "path": dest}
