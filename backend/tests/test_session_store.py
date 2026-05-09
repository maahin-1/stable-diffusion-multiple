import pytest
import os
from storage.session_store import create_session, get_session_path, delete_session, session_exists

def test_create_session_creates_directories(tmp_path):
    session_id = create_session(base=str(tmp_path))
    session_path = get_session_path(session_id, base=str(tmp_path))
    assert os.path.isdir(session_path)
    assert os.path.isdir(os.path.join(session_path, "frames"))
    assert os.path.isdir(os.path.join(session_path, "segments"))
    assert os.path.isdir(os.path.join(session_path, "processed"))
    assert os.path.isdir(os.path.join(session_path, "output"))

def test_session_exists(tmp_path):
    session_id = create_session(base=str(tmp_path))
    assert session_exists(session_id, base=str(tmp_path))
    assert not session_exists("nonexistent", base=str(tmp_path))

def test_delete_session(tmp_path):
    session_id = create_session(base=str(tmp_path))
    delete_session(session_id, base=str(tmp_path))
    assert not session_exists(session_id, base=str(tmp_path))
