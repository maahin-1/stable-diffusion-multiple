import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_run_segmentation(client, tmp_path):
    with patch("routers.segment.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.segment.segment_clothing", return_value="/tmp/mask.png"), \
         patch("routers.segment.detect_persons", return_value=[{"label": "person", "box": {"xmin": 0, "ymin": 0, "xmax": 100, "ymax": 200}}]), \
         patch("routers.segment.list_frames", return_value=[{"index": 1, "path": "/tmp/frame.jpg"}]):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(f"/api/session/{session_id}/segment")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["results"][0]["frame_index"] == 1

@pytest.mark.asyncio
async def test_run_segmentation_no_frames(client, tmp_path):
    with patch("routers.segment.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.segment.list_frames", return_value=[]):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(f"/api/session/{session_id}/segment")
        assert response.status_code == 400
