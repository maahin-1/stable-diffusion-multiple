import os
import re
from storage.session_store import get_session_path

def get_frames_dir(session_id: str, base: str) -> str:
    return os.path.join(get_session_path(session_id, base=base), "frames")

def get_frame_path(session_id: str, index: int, base: str) -> str:
    return os.path.join(get_frames_dir(session_id, base=base), f"frame_{index:05d}.jpg")

def list_frames(session_id: str, base: str) -> list:
    frames_dir = get_frames_dir(session_id, base=base)
    pattern = re.compile(r"frame_(\d{5})\.jpg")
    frames = []
    for filename in sorted(os.listdir(frames_dir)):
        match = pattern.match(filename)
        if match:
            index = int(match.group(1))
            frames.append({
                "index": index,
                "filename": filename,
                "path": os.path.join(frames_dir, filename),
            })
    return frames

def delete_frame(session_id: str, index: int, base: str) -> None:
    path = get_frame_path(session_id, index, base=base)
    if os.path.exists(path):
        os.remove(path)
