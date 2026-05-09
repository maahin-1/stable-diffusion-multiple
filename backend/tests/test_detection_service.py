import pytest
from unittest.mock import patch, MagicMock, mock_open
from services.detection import detect_persons

def test_detect_persons_returns_boxes():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "person", "score": 0.99, "box": {"xmin": 10, "ymin": 20, "xmax": 100, "ymax": 200}},
        {"label": "cat", "score": 0.95, "box": {"xmin": 5, "ymin": 5, "xmax": 50, "ymax": 50}},
    ]
    with patch("services.detection.requests.post", return_value=mock_response), \
         patch("builtins.open", mock_open(read_data=b"fake")):
        result = detect_persons("/fake/frame.jpg", api_token="token")
    assert len(result) == 1
    assert result[0]["label"] == "person"
    assert result[0]["box"]["xmin"] == 10

def test_detect_persons_raises_on_error():
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "error"
    with patch("services.detection.requests.post", return_value=mock_response), \
         patch("builtins.open", mock_open(read_data=b"fake")):
        with pytest.raises(RuntimeError, match="Detection API error"):
            detect_persons("/fake/frame.jpg", api_token="token")
