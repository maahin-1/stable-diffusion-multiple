import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from storage.session_store import session_exists, get_session_path
from storage.frame_store import list_frames
from services.video import reconstruct_video
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["export"])

class ExportRequest(BaseModel):
    quality: str
    fps: int

@router.post("/{session_id}/export")
async def export_video(session_id: str, body: ExportRequest):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    if body.quality not in ("preview", "hq"):
        raise HTTPException(status_code=400, detail="quality must be 'preview' or 'hq'")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    processed_dir = os.path.join(session_path, "processed")
    output_dir = os.path.join(session_path, "output")
    suffix = "preview" if body.quality == "preview" else "hq"
    output_path = os.path.join(output_dir, f"output_{suffix}.mp4")
    reconstruct_video(processed_dir, output_path, fps=body.fps, quality=body.quality)
    return {"quality": body.quality, "path": output_path}

@router.get("/{session_id}/export/download")
async def download_export(session_id: str, quality: str = "hq"):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    suffix = "preview" if quality == "preview" else "hq"
    output_path = os.path.join(session_path, "output", f"output_{suffix}.mp4")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Export not found. Run export first.")
    return FileResponse(output_path, media_type="video/mp4", filename=f"output_{suffix}.mp4")
