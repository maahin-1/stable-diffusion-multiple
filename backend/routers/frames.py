import os
import ffmpeg as ffmpeg_lib
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from storage.session_store import session_exists, get_session_path
from storage.frame_store import list_frames, delete_frame, get_frames_dir, get_frame_path
from services.video import extract_frames
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["frames"])

class ExtractRequest(BaseModel):
    fps: int

@router.post("/{session_id}/extract")
async def extract(session_id: str, body: ExtractRequest):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    video_path = os.path.join(session_path, "video.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="No video uploaded")
    frames_dir = get_frames_dir(session_id, base=BASE_STORAGE)
    try:
        count = extract_frames(video_path, frames_dir, fps=body.fps)
    except ffmpeg_lib.Error as e:
        stderr = e.stderr.decode() if e.stderr else "no stderr"
        raise HTTPException(status_code=500, detail=f"ffmpeg error: {stderr}")
    return {"frame_count": count, "fps": body.fps}

@router.get("/{session_id}/frames")
async def get_frames(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    frames = list_frames(session_id, base=BASE_STORAGE)
    return {"frames": frames}

@router.delete("/{session_id}/frames/{index}")
async def remove_frame(session_id: str, index: int):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    delete_frame(session_id, index, base=BASE_STORAGE)
    return {"deleted": index}

@router.get("/{session_id}/frames/{filename}/image")
async def get_frame_image(session_id: str, filename: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    frames_dir = get_frames_dir(session_id, base=BASE_STORAGE)
    path = os.path.join(frames_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(path, media_type="image/jpeg")
