import pytest
from unittest.mock import patch, MagicMock
from services.segmentation import segment_clothing

def test_segment_clothing_returns_mask(tmp_path):
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("L", (100, 100)).save(buf, format="PNG")
    buf.seek(0)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = buf.read()

    (tmp_path / "frame.jpg").write_bytes(b"fake")

    with patch("services.segmentation.requests.post", return_value=mock_response):
        result = segment_clothing(
            image_path=str(tmp_path / "frame.jpg"),
            output_path=str(tmp_path / "mask.png"),
            api_token="fake-token"
        )
    assert result == str(tmp_path / "mask.png")

def test_segment_clothing_raises_on_api_error():
    import unittest.mock as um
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_open = um.mock_open(read_data=b"fake")
    with patch("builtins.open", mock_open), \
         patch("services.segmentation.requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError, match="Segmentation API error"):
            segment_clothing("/fake/frame.jpg", "/tmp/mask.png", api_token="token")
