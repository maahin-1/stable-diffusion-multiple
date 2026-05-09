import pytest
import io
from PIL import Image
from unittest.mock import patch

@pytest.mark.asyncio
async def test_upload_product(client, tmp_path):
    with patch("routers.products.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        response = await client.post(
            f"/api/session/{session_id}/products",
            data={"tag": "product-1"},
            files={"file": ("shirt_front.jpg", buf.read(), "image/jpeg")}
        )
        assert response.status_code == 200
        assert response.json()["tag"] == "product-1"
        assert response.json()["filename"] == "shirt_front.jpg"

@pytest.mark.asyncio
async def test_list_products(client, tmp_path):
    with patch("routers.products.BASE_STORAGE", str(tmp_path)), \
         patch("routers.sessions.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.get(f"/api/session/{session_id}/products")
        assert response.status_code == 200
        assert "products" in response.json()
