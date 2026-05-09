import pytest
from unittest.mock import patch, MagicMock
from services.video import extract_frames, reconstruct_video

def test_extract_frames_calls_ffmpeg(tmp_path):
    with patch("services.video.ffmpeg") as mock_ffmpeg:
        mock_chain = MagicMock()
        mock_ffmpeg.input.return_value.output.return_value = mock_chain
        extract_frames(
            video_path=str(tmp_path / "test.mp4"),
            output_dir=str(tmp_path / "frames"),
            fps=30
        )
        mock_ffmpeg.input.assert_called_once()

def test_extract_frames_validates_fps():
    with pytest.raises(ValueError, match="FPS must be between"):
        extract_frames("video.mp4", "/tmp", fps=0)
    with pytest.raises(ValueError, match="FPS must be between"):
        extract_frames("video.mp4", "/tmp", fps=120)

def test_reconstruct_video_calls_ffmpeg(tmp_path):
    with patch("services.video.ffmpeg") as mock_ffmpeg:
        mock_chain = MagicMock()
        mock_ffmpeg.input.return_value.output.return_value = mock_chain
        reconstruct_video(
            frames_dir=str(tmp_path),
            output_path=str(tmp_path / "out.mp4"),
            fps=30,
            quality="preview"
        )
        mock_ffmpeg.input.assert_called_once()
