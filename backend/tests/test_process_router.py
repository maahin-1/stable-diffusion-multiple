import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_start_processing(client, tmp_path):
    with patch("routers.process.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)), \
         patch("routers.process.run_inpainting_job", new_callable=AsyncMock):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/process",
            json={
                "assignments": [
                    {"frame_index": 1, "product_tag": "product-1", "product_image": "shirt_front.jpg"}
                ]
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "started"
        assert response.json()["frame_count"] == 1

@pytest.mark.asyncio
async def test_start_processing_nonexistent_session(client, tmp_path):
    with patch("routers.process.BASE_STORAGE", str(tmp_path)):
        response = await client.post(
            "/api/session/nonexistent/process",
            json={"assignments": []}
        )
        assert response.status_code == 404
