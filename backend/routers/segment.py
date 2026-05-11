import os
from fastapi import APIRouter, HTTPException
from storage.session_store import session_exists, get_session_path
from storage.frame_store import list_frames
from services.segmentation import segment_clothing
from services.detection import detect_persons
from config import BASE_STORAGE, HF_API_TOKEN

router = APIRouter(prefix="/api/session", tags=["segment"])

@router.post("/{session_id}/segment")
async def run_segmentation(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    frames = list_frames(session_id, base=BASE_STORAGE)
    if not frames:
        raise HTTPException(status_code=400, detail="No frames extracted")
    segments_dir = os.path.join(get_session_path(session_id, base=BASE_STORAGE), "segments")
    results = []
    for frame in frames:
        mask_path = os.path.join(segments_dir, f"mask_{frame['index']:05d}.png")
        try:
            segment_clothing(frame["path"], mask_path, api_token=HF_API_TOKEN)
            persons = detect_persons(frame["path"], api_token=HF_API_TOKEN)
            flat_persons = [
                {
                    "xmin": p["box"]["xmin"], "ymin": p["box"]["ymin"],
                    "xmax": p["box"]["xmax"], "ymax": p["box"]["ymax"],
                    "score": p["score"],
                }
                for p in persons if "box" in p
            ]
            results.append({
                "frame": frame["filename"],
                "mask_path": mask_path,
                "persons": flat_persons,
                "error": None
            })
        except RuntimeError as e:
            results.append({
                "frame": frame["filename"],
                "mask_path": None,
                "persons": [],
                "error": str(e)
            })
    return {"results": results}
