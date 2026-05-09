import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_upload_video(client, tmp_path):
    with patch("routers.upload.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        video_bytes = b"fake-video-data"
        response = await client.post(
            f"/api/session/{session_id}/upload",
            files={"file": ("test.mp4", video_bytes, "video/mp4")}
        )
        assert response.status_code == 200
        assert response.json()["filename"] == "video.mp4"

@pytest.mark.asyncio
async def test_extract_frames(client, tmp_path):
    with patch("routers.frames.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.frames.extract_frames", return_value=30):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        import os
        session_path = os.path.join(str(tmp_path), session_id)
        os.makedirs(session_path, exist_ok=True)
        open(os.path.join(session_path, "video.mp4"), "wb").close()
        response = await client.post(
            f"/api/session/{session_id}/extract",
            json={"fps": 30}
        )
        assert response.status_code == 200
        assert response.json()["frame_count"] == 30

@pytest.mark.asyncio
async def test_list_frames(client, tmp_path):
    with patch("routers.frames.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.frames.list_frames", return_value=[{"index": 1, "filename": "frame_00001.jpg", "path": "/tmp/frame_00001.jpg"}]):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.get(f"/api/session/{session_id}/frames")
        assert response.status_code == 200
        assert len(response.json()["frames"]) == 1
