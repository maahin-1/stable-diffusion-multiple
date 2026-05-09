import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
from storage.session_store import session_exists
from storage.frame_store import list_frames
from services.job_runner import run_inpainting_job
from routers.ws import broadcast
from config import BASE_STORAGE, REPLICATE_API_TOKEN

router = APIRouter(prefix="/api/session", tags=["process"])

class FrameAssignment(BaseModel):
    frame_index: int
    product_tag: str
    product_image: str

class ProcessRequest(BaseModel):
    assignments: List[FrameAssignment]

@router.post("/{session_id}/process")
async def start_process(session_id: str, body: ProcessRequest, background_tasks: BackgroundTasks):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    assignments = [a.model_dump() for a in body.assignments]

    async def job():
        await run_inpainting_job(
            session_id=session_id,
            base=BASE_STORAGE,
            assignments=assignments,
            api_token=REPLICATE_API_TOKEN,
            on_progress=lambda msg: asyncio.create_task(broadcast(session_id, msg))
        )
        await broadcast(session_id, {"status": "all_complete"})

    background_tasks.add_task(job)
    return {"status": "started", "frame_count": len(assignments)}
