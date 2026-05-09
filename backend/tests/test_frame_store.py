import pytest
import os
from PIL import Image
from storage.frame_store import list_frames, delete_frame, get_frame_path
from storage.session_store import create_session, get_session_path

def test_list_frames_empty(tmp_path):
    session_id = create_session(base=str(tmp_path))
    frames = list_frames(session_id, base=str(tmp_path))
    assert frames == []

def test_list_frames_returns_sorted(tmp_path):
    session_id = create_session(base=str(tmp_path))
    frames_dir = os.path.join(get_session_path(session_id, base=str(tmp_path)), "frames")
    for i in [3, 1, 2]:
        Image.new("RGB", (10, 10)).save(os.path.join(frames_dir, f"frame_{i:05d}.jpg"))
    frames = list_frames(session_id, base=str(tmp_path))
    assert [f["index"] for f in frames] == [1, 2, 3]

def test_delete_frame(tmp_path):
    session_id = create_session(base=str(tmp_path))
    frames_dir = os.path.join(get_session_path(session_id, base=str(tmp_path)), "frames")
    Image.new("RGB", (10, 10)).save(os.path.join(frames_dir, "frame_00001.jpg"))
    delete_frame(session_id, 1, base=str(tmp_path))
    assert list_frames(session_id, base=str(tmp_path)) == []
