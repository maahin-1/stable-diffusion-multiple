from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class Session(BaseModel):
    id: str
    fps: Optional[int] = None
    frame_count: int = 0

class Frame(BaseModel):
    index: int
    filename: str
    path: str

class Product(BaseModel):
    tag: str
    images: List[str]

class FrameJob(BaseModel):
    frame_index: int
    status: JobStatus = JobStatus.pending
    error: Optional[str] = None
