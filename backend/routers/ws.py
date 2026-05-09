import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
_connections: dict = {}

def get_connections(session_id: str) -> list:
    return _connections.get(session_id, [])

async def broadcast(session_id: str, message: dict):
    for ws in list(get_connections(session_id)):
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            _connections[session_id].remove(ws)

@router.websocket("/ws/session/{session_id}/progress")
async def progress_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections[session_id].remove(websocket)
