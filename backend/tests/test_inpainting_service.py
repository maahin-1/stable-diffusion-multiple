import pytest
from unittest.mock import patch, MagicMock, mock_open, call

def _make_img_bytes():
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()

def test_inpaint_frame_returns_output_path(tmp_path):
    output_path = str(tmp_path / "output.jpg")

    post_response = MagicMock()
    post_response.status_code = 201
    post_response.json.return_value = {"id": "abc123", "status": "starting"}

    poll_response = MagicMock()
    poll_response.json.return_value = {
        "status": "succeeded",
        "output": ["https://example.com/result.jpg"]
    }

    img_response = MagicMock()
    img_response.content = _make_img_bytes()

    def side_effect_get(url, **kwargs):
        if "predictions" in url:
            return poll_response
        return img_response

    with patch("services.inpainting.requests.post", return_value=post_response), \
         patch("services.inpainting.requests.get", side_effect=side_effect_get), \
         patch("services.inpainting._encode_image", return_value="data:image/jpeg;base64,fake"):
        from services.inpainting import inpaint_frame
        result = inpaint_frame(
            frame_path="/fake/frame.jpg",
            mask_path="/fake/mask.png",
            product_path="/fake/product.jpg",
            output_path=output_path,
            api_token="r8_fake"
        )
    assert result == output_path

def test_inpaint_frame_raises_on_failure():
    post_response = MagicMock()
    post_response.json.return_value = {"id": "abc123", "status": "starting"}

    poll_response = MagicMock()
    poll_response.json.return_value = {"status": "failed", "error": "Out of memory"}

    with patch("services.inpainting.requests.post", return_value=post_response), \
         patch("services.inpainting.requests.get", return_value=poll_response), \
         patch("services.inpainting._encode_image", return_value="data:image/jpeg;base64,fake"):
        from services.inpainting import inpaint_frame
        with pytest.raises(RuntimeError, match="Inpainting failed"):
            inpaint_frame("/fake/frame.jpg", "/fake/mask.png", "/fake/product.jpg", "/tmp/out.jpg", "r8_fake")
