import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_export_preview(client, tmp_path):
    with patch("routers.export.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.export.reconstruct_video", return_value=str(tmp_path / "out.mp4")):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/export",
            json={"quality": "preview", "fps": 30}
        )
        assert response.status_code == 200
        assert response.json()["quality"] == "preview"

@pytest.mark.asyncio
async def test_export_hq(client, tmp_path):
    with patch("routers.export.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.export.reconstruct_video", return_value=str(tmp_path / "out_hq.mp4")):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/export",
            json={"quality": "hq", "fps": 30}
        )
        assert response.status_code == 200
        assert response.json()["quality"] == "hq"

@pytest.mark.asyncio
async def test_export_invalid_quality(client, tmp_path):
    with patch("routers.export.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/export",
            json={"quality": "ultra", "fps": 30}
        )
        assert response.status_code == 400
