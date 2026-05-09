from fastapi import APIRouter, HTTPException
from storage.session_store import create_session, delete_session, session_exists
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["sessions"])

@router.post("")
async def create_new_session():
    session_id = create_session(base=BASE_STORAGE)
    return {"id": session_id}

@router.delete("/{session_id}")
async def delete_existing_session(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id, base=BASE_STORAGE)
    return {"deleted": session_id}
