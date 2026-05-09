import os
import uuid
import shutil

SUBDIRS = ["frames", "segments", "processed", "output", "products"]

def create_session(base: str) -> str:
    session_id = str(uuid.uuid4())
    session_path = get_session_path(session_id, base=base)
    for subdir in SUBDIRS:
        os.makedirs(os.path.join(session_path, subdir), exist_ok=True)
    return session_id

def get_session_path(session_id: str, base: str) -> str:
    return os.path.join(base, session_id)

def session_exists(session_id: str, base: str) -> bool:
    return os.path.isdir(get_session_path(session_id, base=base))

def delete_session(session_id: str, base: str) -> None:
    session_path = get_session_path(session_id, base=base)
    if os.path.isdir(session_path):
        shutil.rmtree(session_path)
