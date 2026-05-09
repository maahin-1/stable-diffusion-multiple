import pytest

@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 36  # UUID format

@pytest.mark.asyncio
async def test_delete_session(client):
    create_resp = await client.post("/api/session")
    session_id = create_resp.json()["id"]
    delete_resp = await client.delete(f"/api/session/{session_id}")
    assert delete_resp.status_code == 200

@pytest.mark.asyncio
async def test_delete_nonexistent_session(client):
    response = await client.delete("/api/session/nonexistent-id")
    assert response.status_code == 404
