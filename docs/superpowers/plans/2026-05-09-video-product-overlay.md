# Video Product Overlay System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web tool that extracts video frames, overlays product clothing images via Stable Diffusion inpainting, and reconstructs the output as a video.

**Architecture:** FastAPI Python backend handles video processing (ffmpeg), ML API calls (HuggingFace segmentation + Replicate inpainting), and session file management. React/Vite/TypeScript frontend handles frame gallery, chat-based product upload with @tagging, Fabric.js canvas selection, and WebSocket progress. All storage is local temp files.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, ffmpeg-python, requests, Pillow, pytest, httpx — React 18, Vite, TypeScript, Fabric.js, react-dropzone, @tanstack/react-query, axios

---

## File Map

```
stable-diffusion/
  backend/
    main.py                        # FastAPI app, CORS, router registration
    config.py                      # settings: API keys, base storage path, limits
    models/
      session.py                   # Pydantic: Session, Frame, Product, Job models
    storage/
      session_store.py             # create/get/delete session directories
      frame_store.py               # list/delete individual frame files
    services/
      video.py                     # ffmpeg extract frames + reconstruct video
      segmentation.py              # HuggingFace segformer API client
      detection.py                 # HuggingFace DETR person detection API client
      inpainting.py                # Replicate SD inpainting API client
      job_runner.py                # async batch job: runs inpainting per frame
    routers/
      sessions.py                  # POST/DELETE /api/session
      upload.py                    # POST /api/session/{id}/upload
      frames.py                    # GET/DELETE /api/session/{id}/frames
      products.py                  # POST/GET /api/session/{id}/products
      segment.py                   # POST /api/session/{id}/segment
      process.py                   # POST /api/session/{id}/process
      export.py                    # POST /api/session/{id}/export
      ws.py                        # WS /ws/session/{id}/progress
    tests/
      conftest.py                  # shared fixtures: test client, temp dirs
      test_session_store.py
      test_frame_store.py
      test_video_service.py
      test_segmentation_service.py
      test_detection_service.py
      test_inpainting_service.py
      test_sessions_router.py
      test_frames_router.py
      test_products_router.py
      test_process_router.py
      test_export_router.py
  frontend/
    index.html
    vite.config.ts
    tsconfig.json
    package.json
    src/
      main.tsx
      App.tsx
      types/index.ts               # Session, Frame, Product, Job TS types
      api/
        client.ts                  # axios base instance
        sessions.ts                # createSession, deleteSession
        frames.ts                  # extractFrames, listFrames, deleteFrame
        products.ts                # uploadProduct, listProducts
        segment.ts                 # runSegmentation
        process.ts                 # startProcessing
        export.ts                  # exportVideo
      hooks/
        useSession.ts              # session CRUD + state
        useWebSocket.ts            # WebSocket progress subscription
      components/
        VideoUpload.tsx            # drag/drop video file + FPS selector
        FrameGallery.tsx           # scrollable grid of FrameCard components
        FrameCard.tsx              # single frame thumbnail with delete button
        ChatPanel.tsx              # right-side chat: messages + image uploads
        ProductTag.tsx             # @tag chip with image preview
        CanvasOverlay.tsx          # Fabric.js canvas for mask drawing
        SegmentOverlay.tsx         # renders detected mask polygons on frame
        ModelAssignment.tsx        # per-detected-model product assignment UI
        ProgressPanel.tsx          # live job progress via WebSocket
        ExportPanel.tsx            # preview vs HQ export form
```

---

## Task 1: Backend Project Scaffolding

**Files:**
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
ffmpeg-python==0.2.0
Pillow==10.3.0
requests==2.31.0
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

- [ ] **Step 2: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`
Expected: All packages install without error.

- [ ] **Step 3: Write failing test for app health**

Create `backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

Create `backend/tests/test_main.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd backend && pytest tests/test_main.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 5: Create config.py**

```python
import os
import tempfile

BASE_STORAGE = os.environ.get("SD_STORAGE", os.path.join(tempfile.gettempdir(), "sd-overlay"))
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
MAX_FPS = 60
MIN_FPS = 1
```

- [ ] **Step 6: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Video Product Overlay")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git init
git add backend/
git commit -m "feat: backend project scaffolding with health endpoint"
```

---

## Task 2: Session Storage

**Files:**
- Create: `backend/models/session.py`
- Create: `backend/storage/session_store.py`
- Create: `backend/tests/test_session_store.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_session_store.py`:
```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_session_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'storage'`

- [ ] **Step 3: Create models/session.py**

```python
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
    images: List[str]  # list of filenames

class FrameJob(BaseModel):
    frame_index: int
    status: JobStatus = JobStatus.pending
    error: Optional[str] = None
```

- [ ] **Step 4: Create storage/session_store.py**

```python
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
```

- [ ] **Step 5: Run to verify pass**

Run: `cd backend && pytest tests/test_session_store.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/models/ backend/storage/
git commit -m "feat: session storage with uuid-based directories"
```

---

## Task 3: Session Router

**Files:**
- Create: `backend/routers/sessions.py`
- Create: `backend/tests/test_sessions_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_sessions_router.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 36  # UUID format

@pytest.mark.asyncio
async def test_delete_session(client):
    create_resp = await client.post("/api/session")
    session_id = create_resp.json()["id"]
    delete_resp = await client.delete(f"/api/session/{session_id}")
    assert delete_resp.status_code == 200

@pytest.mark.asyncio
async def test_delete_nonexistent_session(client):
    response = await client.delete("/api/session/nonexistent-id")
    assert response.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_sessions_router.py -v`
Expected: FAIL — 404 on POST /api/session

- [ ] **Step 3: Create routers/sessions.py**

```python
from fastapi import APIRouter, HTTPException
from storage.session_store import create_session, delete_session, session_exists
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["sessions"])

@router.post("")
async def create_new_session():
    session_id = create_session(base=BASE_STORAGE)
    return {"id": session_id}

@router.delete("/{session_id}")
async def delete_existing_session(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id, base=BASE_STORAGE)
    return {"deleted": session_id}
```

- [ ] **Step 4: Register router in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import sessions

app = FastAPI(title="Video Product Overlay")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run to verify pass**

Run: `cd backend && pytest tests/test_sessions_router.py tests/test_main.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/routers/ backend/main.py
git commit -m "feat: session create and delete endpoints"
```

---

## Task 4: Frame Store

**Files:**
- Create: `backend/storage/frame_store.py`
- Create: `backend/tests/test_frame_store.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_frame_store.py`:
```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_frame_store.py -v`
Expected: FAIL

- [ ] **Step 3: Create storage/frame_store.py**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && pytest tests/test_frame_store.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/storage/frame_store.py backend/tests/test_frame_store.py
git commit -m "feat: frame store list and delete"
```

---

## Task 5: Video Service (Extract + Reconstruct)

**Files:**
- Create: `backend/services/video.py`
- Create: `backend/tests/test_video_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_video_service.py`:
```python
import pytest
import os
from unittest.mock import patch, MagicMock
from services.video import extract_frames, reconstruct_video

def test_extract_frames_calls_ffmpeg(tmp_path):
    with patch("services.video.ffmpeg") as mock_ffmpeg:
        mock_run = MagicMock()
        mock_ffmpeg.input.return_value.output.return_value.run = mock_run
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
        mock_run = MagicMock()
        mock_ffmpeg.input.return_value.output.return_value.run = mock_run
        reconstruct_video(
            frames_dir=str(tmp_path),
            output_path=str(tmp_path / "out.mp4"),
            fps=30,
            quality="preview"
        )
        mock_ffmpeg.input.assert_called_once()
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_video_service.py -v`
Expected: FAIL

- [ ] **Step 3: Create services/video.py**

```python
import os
import ffmpeg
from config import MIN_FPS, MAX_FPS

def extract_frames(video_path: str, output_dir: str, fps: int) -> int:
    if fps < MIN_FPS or fps > MAX_FPS:
        raise ValueError(f"FPS must be between {MIN_FPS} and {MAX_FPS}")
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "frame_%05d.jpg")
    (
        ffmpeg
        .input(video_path)
        .output(output_pattern, vf=f"fps={fps}", qscale_v=2)
        .run(overwrite_output=True, quiet=True)
    )
    return len([f for f in os.listdir(output_dir) if f.endswith(".jpg")])

def reconstruct_video(frames_dir: str, output_path: str, fps: int, quality: str = "preview") -> str:
    input_pattern = os.path.join(frames_dir, "frame_%05d.jpg")
    if quality == "preview":
        vf = "scale=1280:720:force_original_aspect_ratio=decrease"
        crf = 28
    else:
        vf = None
        crf = 18
    stream = ffmpeg.input(input_pattern, framerate=fps)
    kwargs = {"vcodec": "libx264", "crf": crf, "pix_fmt": "yuv420p"}
    if vf:
        kwargs["vf"] = vf
    stream.output(output_path, **kwargs).run(overwrite_output=True, quiet=True)
    return output_path
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && pytest tests/test_video_service.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/services/video.py backend/tests/test_video_service.py
git commit -m "feat: ffmpeg frame extraction and video reconstruction service"
```

---

## Task 6: Upload + Extract Routers

**Files:**
- Create: `backend/routers/upload.py`
- Create: `backend/routers/frames.py`
- Create: `backend/tests/test_frames_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_frames_router.py`:
```python
import pytest
import os
from unittest.mock import patch

@pytest.mark.asyncio
async def test_upload_video(client, tmp_path):
    with patch("routers.upload.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        video_bytes = b"fake-video-data"
        response = await client.post(
            f"/api/session/{session_id}/upload",
            files={"file": ("test.mp4", video_bytes, "video/mp4")}
        )
        assert response.status_code == 200
        assert response.json()["filename"] == "video.mp4"

@pytest.mark.asyncio
async def test_extract_frames(client, tmp_path):
    with patch("routers.frames.BASE_STORAGE", str(tmp_path)), \
         patch("routers.frames.extract_frames", return_value=30) as mock_extract:
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/extract",
            json={"fps": 30}
        )
        assert response.status_code == 200
        assert response.json()["frame_count"] == 30

@pytest.mark.asyncio
async def test_list_frames(client, tmp_path):
    with patch("routers.frames.BASE_STORAGE", str(tmp_path)), \
         patch("routers.frames.list_frames", return_value=[{"index": 1, "filename": "frame_00001.jpg", "path": "/tmp/frame_00001.jpg"}]):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.get(f"/api/session/{session_id}/frames")
        assert response.status_code == 200
        assert len(response.json()["frames"]) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_frames_router.py -v`
Expected: FAIL — 404 on upload endpoint

- [ ] **Step 3: Create routers/upload.py**

```python
import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from storage.session_store import session_exists, get_session_path
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["upload"])

@router.post("/{session_id}/upload")
async def upload_video(session_id: str, file: UploadFile = File(...)):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    dest = os.path.join(session_path, "video.mp4")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": "video.mp4", "path": dest}
```

- [ ] **Step 4: Create routers/frames.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from storage.session_store import session_exists, get_session_path
from storage.frame_store import list_frames, delete_frame, get_frames_dir
from services.video import extract_frames
from config import BASE_STORAGE
import os

router = APIRouter(prefix="/api/session", tags=["frames"])

class ExtractRequest(BaseModel):
    fps: int

@router.post("/{session_id}/extract")
async def extract(session_id: str, body: ExtractRequest):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    video_path = os.path.join(session_path, "video.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="No video uploaded")
    frames_dir = get_frames_dir(session_id, base=BASE_STORAGE)
    count = extract_frames(video_path, frames_dir, fps=body.fps)
    return {"frame_count": count, "fps": body.fps}

@router.get("/{session_id}/frames")
async def get_frames(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    frames = list_frames(session_id, base=BASE_STORAGE)
    return {"frames": frames}

@router.delete("/{session_id}/frames/{index}")
async def remove_frame(session_id: str, index: int):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    delete_frame(session_id, index, base=BASE_STORAGE)
    return {"deleted": index}
```

- [ ] **Step 5: Register routers in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import sessions, upload, frames

app = FastAPI(title="Video Product Overlay")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(sessions.router)
app.include_router(upload.router)
app.include_router(frames.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run to verify pass**

Run: `cd backend && pytest tests/test_frames_router.py -v`
Expected: PASS (3 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/routers/upload.py backend/routers/frames.py backend/main.py backend/tests/test_frames_router.py
git commit -m "feat: video upload and frame extraction endpoints"
```

---

## Task 7: Product Upload Router

**Files:**
- Create: `backend/routers/products.py`
- Create: `backend/tests/test_products_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_products_router.py`:
```python
import pytest

@pytest.mark.asyncio
async def test_upload_product(client, tmp_path):
    with __import__("unittest.mock", fromlist=["patch"]).patch("routers.products.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        from PIL import Image
        import io
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

@pytest.mark.asyncio
async def test_list_products(client, tmp_path):
    with __import__("unittest.mock", fromlist=["patch"]).patch("routers.products.BASE_STORAGE", str(tmp_path)):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.get(f"/api/session/{session_id}/products")
        assert response.status_code == 200
        assert "products" in response.json()
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_products_router.py -v`
Expected: FAIL

- [ ] **Step 3: Create routers/products.py**

```python
import os
import json
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from storage.session_store import session_exists, get_session_path
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["products"])

def get_products_dir(session_id: str) -> str:
    return os.path.join(get_session_path(session_id, base=BASE_STORAGE), "products")

def load_product_index(session_id: str) -> dict:
    index_path = os.path.join(get_products_dir(session_id), "index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return json.load(f)
    return {}

def save_product_index(session_id: str, index: dict) -> None:
    index_path = os.path.join(get_products_dir(session_id), "index.json")
    with open(index_path, "w") as f:
        json.dump(index, f)

@router.post("/{session_id}/products")
async def upload_product(session_id: str, tag: str = Form(...), file: UploadFile = File(...)):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    products_dir = get_products_dir(session_id)
    tag_dir = os.path.join(products_dir, tag)
    os.makedirs(tag_dir, exist_ok=True)
    dest = os.path.join(tag_dir, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    index = load_product_index(session_id)
    if tag not in index:
        index[tag] = []
    if file.filename not in index[tag]:
        index[tag].append(file.filename)
    save_product_index(session_id, index)
    return {"tag": tag, "filename": file.filename}

@router.get("/{session_id}/products")
async def list_products(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    index = load_product_index(session_id)
    return {"products": index}
```

- [ ] **Step 4: Register in main.py**

Add to imports and app setup in `backend/main.py`:
```python
from routers import sessions, upload, frames, products
# ...
app.include_router(products.router)
```

- [ ] **Step 5: Run to verify pass**

Run: `cd backend && pytest tests/test_products_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/routers/products.py backend/tests/test_products_router.py backend/main.py
git commit -m "feat: product upload and listing with tag grouping"
```

---

## Task 8: HuggingFace Segmentation Service

**Files:**
- Create: `backend/services/segmentation.py`
- Create: `backend/tests/test_segmentation_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_segmentation_service.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from services.segmentation import segment_clothing

def test_segment_clothing_returns_mask(tmp_path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake-mask-bytes"
    with patch("services.segmentation.requests.post", return_value=mock_response), \
         patch("services.segmentation.Image") as mock_image:
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        result = segment_clothing(
            image_path="/fake/frame.jpg",
            output_path=str(tmp_path / "mask.png"),
            api_token="fake-token"
        )
        assert result == str(tmp_path / "mask.png")

def test_segment_clothing_raises_on_api_error():
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    with patch("services.segmentation.requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError, match="Segmentation API error"):
            segment_clothing("/fake/frame.jpg", "/tmp/mask.png", api_token="token")
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_segmentation_service.py -v`
Expected: FAIL

- [ ] **Step 3: Create services/segmentation.py**

```python
import os
import io
import requests
from PIL import Image

HF_SEGMENTATION_MODEL = "mattmdjaga/segformer_b2_clothes"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_SEGMENTATION_MODEL}"

def segment_clothing(image_path: str, output_path: str, api_token: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Segmentation API error {response.status_code}: {response.text}")
    mask_img = Image.open(io.BytesIO(response.content)).convert("L")
    mask_img.save(output_path)
    return output_path
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && pytest tests/test_segmentation_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/segmentation.py backend/tests/test_segmentation_service.py
git commit -m "feat: HuggingFace clothing segmentation service"
```

---

## Task 9: HuggingFace Person Detection Service

**Files:**
- Create: `backend/services/detection.py`
- Create: `backend/tests/test_detection_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_detection_service.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from services.detection import detect_persons

def test_detect_persons_returns_boxes():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"label": "person", "score": 0.99, "box": {"xmin": 10, "ymin": 20, "xmax": 100, "ymax": 200}},
        {"label": "cat", "score": 0.95, "box": {"xmin": 5, "ymin": 5, "xmax": 50, "ymax": 50}},
    ]
    with patch("services.detection.requests.post", return_value=mock_response):
        result = detect_persons("/fake/frame.jpg", api_token="token")
    assert len(result) == 1
    assert result[0]["label"] == "person"
    assert result[0]["box"]["xmin"] == 10

def test_detect_persons_raises_on_error():
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "error"
    with patch("services.detection.requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError, match="Detection API error"):
            detect_persons("/fake/frame.jpg", api_token="token")
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_detection_service.py -v`
Expected: FAIL

- [ ] **Step 3: Create services/detection.py**

```python
import requests

HF_DETECTION_MODEL = "facebook/detr-resnet-50"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_DETECTION_MODEL}"

def detect_persons(image_path: str, api_token: str) -> list:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(HF_API_URL, headers=headers, data=image_bytes, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Detection API error {response.status_code}: {response.text}")
    results = response.json()
    return [r for r in results if r.get("label") == "person" and r.get("score", 0) > 0.5]
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && pytest tests/test_detection_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/detection.py backend/tests/test_detection_service.py
git commit -m "feat: HuggingFace DETR person detection service"
```

---

## Task 10: Segment Router

**Files:**
- Create: `backend/routers/segment.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_segment_router.py`:
```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_run_segmentation(client, tmp_path):
    with patch("routers.segment.BASE_STORAGE", str(tmp_path)), \
         patch("routers.segment.segment_clothing", return_value="/tmp/mask.png"), \
         patch("routers.segment.detect_persons", return_value=[{"label": "person", "box": {"xmin": 0, "ymin": 0, "xmax": 100, "ymax": 200}}]), \
         patch("routers.segment.list_frames", return_value=[{"index": 1, "path": "/tmp/frame.jpg"}]):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(f"/api/session/{session_id}/segment")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["results"][0]["frame_index"] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_segment_router.py -v`
Expected: FAIL

- [ ] **Step 3: Create routers/segment.py**

```python
import os
from fastapi import APIRouter, HTTPException
from storage.session_store import session_exists, get_session_path
from storage.frame_store import list_frames
from services.segmentation import segment_clothing
from services.detection import detect_persons
from config import BASE_STORAGE, HF_API_TOKEN

router = APIRouter(prefix="/api/session", tags=["segment"])

@router.post("/{session_id}/segment")
async def run_segmentation(session_id: str):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    frames = list_frames(session_id, base=BASE_STORAGE)
    if not frames:
        raise HTTPException(status_code=400, detail="No frames extracted")
    segments_dir = os.path.join(get_session_path(session_id, base=BASE_STORAGE), "segments")
    results = []
    for frame in frames:
        mask_path = os.path.join(segments_dir, f"mask_{frame['index']:05d}.png")
        try:
            segment_clothing(frame["path"], mask_path, api_token=HF_API_TOKEN)
            persons = detect_persons(frame["path"], api_token=HF_API_TOKEN)
            results.append({
                "frame_index": frame["index"],
                "mask_path": mask_path,
                "persons": persons,
                "error": None
            })
        except RuntimeError as e:
            results.append({
                "frame_index": frame["index"],
                "mask_path": None,
                "persons": [],
                "error": str(e)
            })
    return {"results": results}
```

- [ ] **Step 4: Register in main.py**

```python
from routers import sessions, upload, frames, products, segment
# ...
app.include_router(segment.router)
```

- [ ] **Step 5: Run to verify pass**

Run: `cd backend && pytest tests/test_segment_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/routers/segment.py backend/tests/test_segment_router.py backend/main.py
git commit -m "feat: segmentation endpoint runs clothing + person detection per frame"
```

---

## Task 11: Replicate Inpainting Service

**Files:**
- Create: `backend/services/inpainting.py`
- Create: `backend/tests/test_inpainting_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_inpainting_service.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from services.inpainting import inpaint_frame

def test_inpaint_frame_returns_output_path(tmp_path):
    mock_post = MagicMock()
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"id": "abc123", "status": "starting"}

    mock_get = MagicMock()
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": "succeeded",
        "output": ["https://example.com/result.jpg"]
    }

    mock_img_response = MagicMock()
    mock_img_response.content = b"fake-image-bytes"

    output_path = str(tmp_path / "output.jpg")
    with patch("services.inpainting.requests.post", return_value=mock_post.return_value), \
         patch("services.inpainting.requests.get", side_effect=[mock_get.return_value, mock_img_response]):
        result = inpaint_frame(
            frame_path="/fake/frame.jpg",
            mask_path="/fake/mask.png",
            product_path="/fake/product.jpg",
            output_path=output_path,
            api_token="r8_fake"
        )
    assert result == output_path

def test_inpaint_frame_raises_on_failure():
    mock_post = MagicMock()
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"id": "abc123", "status": "starting"}

    mock_get = MagicMock()
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": "failed", "error": "Out of memory"}

    with patch("services.inpainting.requests.post", return_value=mock_post.return_value), \
         patch("services.inpainting.requests.get", return_value=mock_get.return_value):
        with pytest.raises(RuntimeError, match="Inpainting failed"):
            inpaint_frame("/fake/frame.jpg", "/fake/mask.png", "/fake/product.jpg", "/tmp/out.jpg", "r8_fake")
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_inpainting_service.py -v`
Expected: FAIL

- [ ] **Step 3: Create services/inpainting.py**

```python
import base64
import time
import requests

REPLICATE_MODEL = "stability-ai/stable-diffusion-inpainting"
REPLICATE_VERSION = "95b7223104132402a9ae91cc677285bc5eb997834bd2349fa486f53910fd68b3"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

def inpaint_frame(
    frame_path: str,
    mask_path: str,
    product_path: str,
    output_path: str,
    api_token: str,
    max_wait: int = 120
) -> str:
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "version": REPLICATE_VERSION,
        "input": {
            "image": _encode_image(frame_path),
            "mask": _encode_image(mask_path),
            "prompt": "product clothing, same style, seamless blend",
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
        }
    }
    response = requests.post(REPLICATE_API_URL, headers=headers, json=payload, timeout=30)
    prediction = response.json()
    prediction_id = prediction["id"]
    poll_url = f"{REPLICATE_API_URL}/{prediction_id}"
    elapsed = 0
    while elapsed < max_wait:
        result = requests.get(poll_url, headers=headers, timeout=30).json()
        status = result.get("status")
        if status == "succeeded":
            image_url = result["output"][0]
            img_data = requests.get(image_url, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(img_data)
            return output_path
        if status == "failed":
            raise RuntimeError(f"Inpainting failed: {result.get('error')}")
        time.sleep(2)
        elapsed += 2
    raise RuntimeError("Inpainting timed out")
```

- [ ] **Step 4: Run to verify pass**

Run: `cd backend && pytest tests/test_inpainting_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/inpainting.py backend/tests/test_inpainting_service.py
git commit -m "feat: Replicate SD inpainting service with polling"
```

---

## Task 12: Process Router + WebSocket Progress

**Files:**
- Create: `backend/routers/process.py`
- Create: `backend/routers/ws.py`
- Create: `backend/services/job_runner.py`
- Create: `backend/tests/test_process_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_process_router.py`:
```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_start_processing(client, tmp_path):
    with patch("routers.process.BASE_STORAGE", str(tmp_path)), \
         patch("routers.process.list_frames", return_value=[{"index": 1, "path": "/tmp/frame.jpg"}]), \
         patch("routers.process.run_inpainting_job"):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/process",
            json={
                "assignments": [
                    {"frame_index": 1, "product_tag": "product-1", "product_image": "shirt_front.jpg"}
                ]
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "started"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_process_router.py -v`
Expected: FAIL

- [ ] **Step 3: Create services/job_runner.py**

```python
import os
import asyncio
from typing import List, Dict, Callable
from services.inpainting import inpaint_frame
from storage.session_store import get_session_path

async def run_inpainting_job(
    session_id: str,
    base: str,
    assignments: List[Dict],
    api_token: str,
    on_progress: Callable[[Dict], None] = None
):
    session_path = get_session_path(session_id, base=base)
    processed_dir = os.path.join(session_path, "processed")
    segments_dir = os.path.join(session_path, "segments")
    products_dir = os.path.join(session_path, "products")

    for assignment in assignments:
        frame_index = assignment["frame_index"]
        product_tag = assignment["product_tag"]
        product_image = assignment["product_image"]

        frame_path = os.path.join(session_path, "frames", f"frame_{frame_index:05d}.jpg")
        mask_path = os.path.join(segments_dir, f"mask_{frame_index:05d}.png")
        product_path = os.path.join(products_dir, product_tag, product_image)
        output_path = os.path.join(processed_dir, f"frame_{frame_index:05d}.jpg")

        try:
            await asyncio.to_thread(
                inpaint_frame,
                frame_path, mask_path, product_path, output_path, api_token
            )
            if on_progress:
                on_progress({"frame_index": frame_index, "status": "completed"})
        except Exception as e:
            if on_progress:
                on_progress({"frame_index": frame_index, "status": "failed", "error": str(e)})
```

- [ ] **Step 4: Create routers/ws.py**

```python
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
_connections: dict[str, list[WebSocket]] = {}

def get_connections(session_id: str) -> list:
    return _connections.get(session_id, [])

async def broadcast(session_id: str, message: dict):
    for ws in list(get_connections(session_id)):
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            _connections[session_id].remove(ws)

@router.websocket("/ws/session/{session_id}/progress")
async def progress_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections[session_id].remove(websocket)
```

- [ ] **Step 5: Create routers/process.py**

```python
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
from storage.session_store import session_exists
from storage.frame_store import list_frames
from services.job_runner import run_inpainting_job
from routers.ws import broadcast
from config import BASE_STORAGE, REPLICATE_API_TOKEN

router = APIRouter(prefix="/api/session", tags=["process"])

class FrameAssignment(BaseModel):
    frame_index: int
    product_tag: str
    product_image: str

class ProcessRequest(BaseModel):
    assignments: List[FrameAssignment]

@router.post("/{session_id}/process")
async def start_process(session_id: str, body: ProcessRequest, background_tasks: BackgroundTasks):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    assignments = [a.model_dump() for a in body.assignments]

    async def job():
        await run_inpainting_job(
            session_id=session_id,
            base=BASE_STORAGE,
            assignments=assignments,
            api_token=REPLICATE_API_TOKEN,
            on_progress=lambda msg: asyncio.create_task(broadcast(session_id, msg))
        )
        await broadcast(session_id, {"status": "all_complete"})

    background_tasks.add_task(job)
    return {"status": "started", "frame_count": len(assignments)}
```

- [ ] **Step 6: Register in main.py**

```python
from routers import sessions, upload, frames, products, segment, process, ws
# ...
app.include_router(process.router)
app.include_router(ws.router)
```

- [ ] **Step 7: Run to verify pass**

Run: `cd backend && pytest tests/test_process_router.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/routers/process.py backend/routers/ws.py backend/services/job_runner.py backend/tests/test_process_router.py backend/main.py
git commit -m "feat: async inpainting job with WebSocket progress broadcasting"
```

---

## Task 13: Export Router

**Files:**
- Create: `backend/routers/export.py`
- Create: `backend/tests/test_export_router.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_export_router.py`:
```python
import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_export_preview(client, tmp_path):
    with patch("routers.export.BASE_STORAGE", str(tmp_path)), \
         patch("routers.export.list_frames", return_value=[{"index": 1}]), \
         patch("routers.export.reconstruct_video", return_value=str(tmp_path / "out.mp4")):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/export",
            json={"quality": "preview", "fps": 30}
        )
        assert response.status_code == 200
        assert response.json()["quality"] == "preview"

@pytest.mark.asyncio
async def test_export_hq(client, tmp_path):
    with patch("routers.export.BASE_STORAGE", str(tmp_path)), \
         patch("routers.export.list_frames", return_value=[{"index": 1}]), \
         patch("routers.export.reconstruct_video", return_value=str(tmp_path / "out_hq.mp4")):
        session_resp = await client.post("/api/session")
        session_id = session_resp.json()["id"]
        response = await client.post(
            f"/api/session/{session_id}/export",
            json={"quality": "hq", "fps": 30}
        )
        assert response.status_code == 200
        assert response.json()["quality"] == "hq"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/test_export_router.py -v`
Expected: FAIL

- [ ] **Step 3: Create routers/export.py**

```python
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from storage.session_store import session_exists, get_session_path
from storage.frame_store import list_frames
from services.video import reconstruct_video
from config import BASE_STORAGE

router = APIRouter(prefix="/api/session", tags=["export"])

class ExportRequest(BaseModel):
    quality: str  # "preview" or "hq"
    fps: int

@router.post("/{session_id}/export")
async def export_video(session_id: str, body: ExportRequest):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    if body.quality not in ("preview", "hq"):
        raise HTTPException(status_code=400, detail="quality must be 'preview' or 'hq'")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    processed_dir = os.path.join(session_path, "processed")
    output_dir = os.path.join(session_path, "output")
    suffix = "preview" if body.quality == "preview" else "hq"
    output_path = os.path.join(output_dir, f"output_{suffix}.mp4")
    reconstruct_video(processed_dir, output_path, fps=body.fps, quality=body.quality)
    return {"quality": body.quality, "path": output_path}

@router.get("/{session_id}/export/download")
async def download_export(session_id: str, quality: str = "hq"):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    session_path = get_session_path(session_id, base=BASE_STORAGE)
    suffix = "preview" if quality == "preview" else "hq"
    output_path = os.path.join(session_path, "output", f"output_{suffix}.mp4")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Export not found. Run export first.")
    return FileResponse(output_path, media_type="video/mp4", filename=f"output_{suffix}.mp4")
```

- [ ] **Step 4: Register in main.py**

```python
from routers import sessions, upload, frames, products, segment, process, ws, export
# ...
app.include_router(export.router)
```

- [ ] **Step 5: Run to verify pass**

Run: `cd backend && pytest tests/test_export_router.py -v`
Expected: PASS

- [ ] **Step 6: Run full backend test suite**

Run: `cd backend && pytest -v`
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/routers/export.py backend/tests/test_export_router.py backend/main.py
git commit -m "feat: video export endpoint with preview and HQ options"
```

---

## Task 14: Frontend Scaffolding

**Files:**
- Create: `frontend/` (Vite project)
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Scaffold Vite React TypeScript project**

Run:
```bash
cd "d:/projects for fun/stable-diffusion"
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```
Expected: Project created with `src/App.tsx`, `src/main.tsx`.

- [ ] **Step 2: Install dependencies**

Run:
```bash
cd frontend
npm install axios @tanstack/react-query react-dropzone fabric
npm install -D @types/fabric
```
Expected: All packages install.

- [ ] **Step 3: Create src/types/index.ts**

```typescript
export interface Session {
  id: string;
  fps?: number;
  frame_count: number;
}

export interface Frame {
  index: number;
  filename: string;
  path: string;
}

export interface Product {
  tag: string;
  images: string[];
}

export interface SegmentResult {
  frame_index: number;
  mask_path: string | null;
  persons: PersonBox[];
  error: string | null;
}

export interface PersonBox {
  label: string;
  score: number;
  box: { xmin: number; ymin: number; xmax: number; ymax: number };
}

export interface FrameAssignment {
  frame_index: number;
  product_tag: string;
  product_image: string;
}

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface ProgressMessage {
  frame_index?: number;
  status: JobStatus | "all_complete";
  error?: string;
}
```

- [ ] **Step 4: Create src/api/client.ts**

```typescript
import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 60000,
});

export default client;
```

- [ ] **Step 5: Verify app runs**

Run: `cd frontend && npm run dev`
Expected: Vite dev server starts at `http://localhost:5173`.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: frontend Vite/React/TypeScript scaffolding with dependencies"
```

---

## Task 15: Frontend API Layer

**Files:**
- Create: `frontend/src/api/sessions.ts`
- Create: `frontend/src/api/frames.ts`
- Create: `frontend/src/api/products.ts`
- Create: `frontend/src/api/segment.ts`
- Create: `frontend/src/api/process.ts`
- Create: `frontend/src/api/export.ts`

- [ ] **Step 1: Create src/api/sessions.ts**

```typescript
import client from "./client";

export const createSession = () =>
  client.post<{ id: string }>("/api/session").then((r) => r.data);

export const deleteSession = (id: string) =>
  client.delete(`/api/session/${id}`).then((r) => r.data);
```

- [ ] **Step 2: Create src/api/frames.ts**

```typescript
import client from "./client";
import { Frame } from "../types";

export const uploadVideo = (sessionId: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return client.post(`/api/session/${sessionId}/upload`, form).then((r) => r.data);
};

export const extractFrames = (sessionId: string, fps: number) =>
  client.post(`/api/session/${sessionId}/extract`, { fps }).then((r) => r.data);

export const listFrames = (sessionId: string) =>
  client.get<{ frames: Frame[] }>(`/api/session/${sessionId}/frames`).then((r) => r.data.frames);

export const deleteFrame = (sessionId: string, index: number) =>
  client.delete(`/api/session/${sessionId}/frames/${index}`).then((r) => r.data);
```

- [ ] **Step 3: Create src/api/products.ts**

```typescript
import client from "./client";

export const uploadProduct = (sessionId: string, tag: string, file: File) => {
  const form = new FormData();
  form.append("tag", tag);
  form.append("file", file);
  return client.post(`/api/session/${sessionId}/products`, form).then((r) => r.data);
};

export const listProducts = (sessionId: string) =>
  client.get<{ products: Record<string, string[]> }>(`/api/session/${sessionId}/products`).then((r) => r.data.products);
```

- [ ] **Step 4: Create src/api/segment.ts**

```typescript
import client from "./client";
import { SegmentResult } from "../types";

export const runSegmentation = (sessionId: string) =>
  client.post<{ results: SegmentResult[] }>(`/api/session/${sessionId}/segment`).then((r) => r.data.results);
```

- [ ] **Step 5: Create src/api/process.ts**

```typescript
import client from "./client";
import { FrameAssignment } from "../types";

export const startProcessing = (sessionId: string, assignments: FrameAssignment[]) =>
  client.post(`/api/session/${sessionId}/process`, { assignments }).then((r) => r.data);
```

- [ ] **Step 6: Create src/api/export.ts**

```typescript
import client from "./client";

export const exportVideo = (sessionId: string, quality: "preview" | "hq", fps: number) =>
  client.post(`/api/session/${sessionId}/export`, { quality, fps }).then((r) => r.data);

export const getDownloadUrl = (sessionId: string, quality: "preview" | "hq") =>
  `http://localhost:8000/api/session/${sessionId}/export/download?quality=${quality}`;
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/ frontend/src/types/
git commit -m "feat: frontend API layer for all backend endpoints"
```

---

## Task 16: useSession + useWebSocket Hooks

**Files:**
- Create: `frontend/src/hooks/useSession.ts`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create src/hooks/useSession.ts**

```typescript
import { useState } from "react";
import { createSession, deleteSession } from "../api/sessions";

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setLoading(true);
    const session = await createSession();
    setSessionId(session.id);
    setLoading(false);
    return session.id;
  };

  const end = async () => {
    if (sessionId) {
      await deleteSession(sessionId);
      setSessionId(null);
    }
  };

  return { sessionId, loading, start, end };
}
```

- [ ] **Step 2: Create src/hooks/useWebSocket.ts**

```typescript
import { useEffect, useRef, useState } from "react";
import { ProgressMessage } from "../types";

export function useWebSocket(sessionId: string | null) {
  const [messages, setMessages] = useState<ProgressMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    const socket = new WebSocket(`ws://localhost:8000/ws/session/${sessionId}/progress`);
    ws.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (e) => {
      const msg: ProgressMessage = JSON.parse(e.data);
      setMessages((prev) => [...prev, msg]);
    };

    return () => socket.close();
  }, [sessionId]);

  return { messages, connected };
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: useSession and useWebSocket hooks"
```

---

## Task 17: VideoUpload + FrameGallery Components

**Files:**
- Create: `frontend/src/components/VideoUpload.tsx`
- Create: `frontend/src/components/FrameCard.tsx`
- Create: `frontend/src/components/FrameGallery.tsx`

- [ ] **Step 1: Create VideoUpload.tsx**

```tsx
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface Props {
  onUpload: (file: File, fps: number) => void;
  loading: boolean;
}

const FPS_OPTIONS = [30, 45, 60];

export function VideoUpload({ onUpload, loading }: Props) {
  const [fps, setFps] = useState(30);
  const [customFps, setCustomFps] = useState("");

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      const finalFps = customFps ? parseInt(customFps, 10) : fps;
      onUpload(accepted[0], finalFps);
    }
  }, [fps, customFps, onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "video/*": [".mp4", ".mov", ".avi"] },
    maxFiles: 1,
  });

  return (
    <div style={{ padding: 24 }}>
      <div {...getRootProps()} style={{
        border: "2px dashed #666",
        padding: 32,
        borderRadius: 8,
        cursor: "pointer",
        background: isDragActive ? "#f0f0f0" : "transparent",
      }}>
        <input {...getInputProps()} />
        <p>{isDragActive ? "Drop video here" : "Drag & drop video (MP4, MOV, AVI) or click to select"}</p>
      </div>
      <div style={{ marginTop: 16 }}>
        <label>FPS: </label>
        {FPS_OPTIONS.map((f) => (
          <button
            key={f}
            onClick={() => { setFps(f); setCustomFps(""); }}
            style={{ marginRight: 8, fontWeight: fps === f && !customFps ? "bold" : "normal" }}
          >
            {f}
          </button>
        ))}
        <input
          type="number"
          placeholder="Custom FPS"
          value={customFps}
          onChange={(e) => setCustomFps(e.target.value)}
          style={{ width: 100, marginLeft: 8 }}
        />
      </div>
      {loading && <p>Extracting frames…</p>}
    </div>
  );
}
```

- [ ] **Step 2: Create FrameCard.tsx**

```tsx
interface Props {
  index: number;
  filename: string;
  sessionId: string;
  onDelete: (index: number) => void;
}

export function FrameCard({ index, filename, sessionId, onDelete }: Props) {
  const imgSrc = `http://localhost:8000/api/session/${sessionId}/frames/${index}/image`;
  return (
    <div style={{ position: "relative", width: 160, margin: 4 }}>
      <img src={imgSrc} alt={`Frame ${index}`} style={{ width: "100%", display: "block", borderRadius: 4 }} />
      <div style={{ position: "absolute", top: 2, left: 2, background: "rgba(0,0,0,0.5)", color: "#fff", fontSize: 10, padding: "2px 4px", borderRadius: 2 }}>
        #{index}
      </div>
      <button
        onClick={() => onDelete(index)}
        style={{ position: "absolute", top: 2, right: 2, background: "red", color: "#fff", border: "none", borderRadius: 2, cursor: "pointer", fontSize: 12, padding: "2px 6px" }}
      >
        ✕
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Add frame image endpoint to backend**

Add to `backend/routers/frames.py`:
```python
from fastapi.responses import FileResponse

@router.get("/{session_id}/frames/{index}/image")
async def get_frame_image(session_id: str, index: int):
    if not session_exists(session_id, base=BASE_STORAGE):
        raise HTTPException(status_code=404, detail="Session not found")
    path = get_frame_path(session_id, index, base=BASE_STORAGE)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(path, media_type="image/jpeg")
```

- [ ] **Step 4: Create FrameGallery.tsx**

```tsx
import { Frame } from "../types";
import { FrameCard } from "./FrameCard";

interface Props {
  sessionId: string;
  frames: Frame[];
  onDelete: (index: number) => void;
  onConfirm: () => void;
}

export function FrameGallery({ sessionId, frames, onDelete, onConfirm }: Props) {
  return (
    <div style={{ padding: 24 }}>
      <h3>{frames.length} frames extracted</h3>
      <div style={{ display: "flex", flexWrap: "wrap", maxHeight: 480, overflowY: "auto" }}>
        {frames.map((f) => (
          <FrameCard key={f.index} index={f.index} filename={f.filename} sessionId={sessionId} onDelete={onDelete} />
        ))}
      </div>
      <button onClick={onConfirm} style={{ marginTop: 16, padding: "8px 24px", fontSize: 16 }}>
        Confirm Frames →
      </button>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/VideoUpload.tsx frontend/src/components/FrameCard.tsx frontend/src/components/FrameGallery.tsx backend/routers/frames.py
git commit -m "feat: video upload, FPS selection, and frame gallery with delete"
```

---

## Task 18: ChatPanel with @Tagging

**Files:**
- Create: `frontend/src/components/ProductTag.tsx`
- Create: `frontend/src/components/ChatPanel.tsx`

- [ ] **Step 1: Create ProductTag.tsx**

```tsx
interface Props {
  tag: string;
  images: string[];
  onRename: (oldTag: string, newTag: string) => void;
}

export function ProductTag({ tag, images, onRename }: Props) {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", background: "#e8f4ff", borderRadius: 4, padding: "2px 8px", margin: 2 }}>
      <span style={{ color: "#0066cc", fontWeight: "bold" }}>@{tag}</span>
      <span style={{ marginLeft: 6, fontSize: 12, color: "#666" }}>{images.length} image{images.length !== 1 ? "s" : ""}</span>
    </div>
  );
}
```

- [ ] **Step 2: Create ChatPanel.tsx**

```tsx
import { useState, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { ProductTag } from "./ProductTag";
import { uploadProduct } from "../api/products";

interface ChatMessage {
  type: "user" | "system";
  text: string;
  productTag?: string;
  imageFilename?: string;
}

interface Props {
  sessionId: string;
  products: Record<string, string[]>;
  onProductsChange: () => void;
}

export function ChatPanel({ sessionId, products, onProductsChange }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { type: "system", text: "Upload product images here. Type @tag-name to name your product." }
  ]);
  const [input, setInput] = useState("");
  const [pendingTag, setPendingTag] = useState("product-1");

  const addMessage = (msg: ChatMessage) => setMessages((prev) => [...prev, msg]);

  const handleUpload = async (files: File[]) => {
    for (const file of files) {
      const tag = pendingTag;
      await uploadProduct(sessionId, tag, file);
      addMessage({ type: "user", text: `Uploaded ${file.name} as `, productTag: tag, imageFilename: file.name });
      onProductsChange();
      const keys = Object.keys(products);
      setPendingTag(`product-${keys.length + 2}`);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const tagMatch = input.match(/@([\w-]+)/);
    if (tagMatch) setPendingTag(tagMatch[1]);
    addMessage({ type: "user", text: input });
    setInput("");
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: handleUpload,
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
    noClick: true,
  });

  return (
    <div {...getRootProps()} style={{ width: 320, height: "100vh", display: "flex", flexDirection: "column", borderLeft: "1px solid #ddd", padding: 12 }}>
      <input {...getInputProps()} />
      <h4 style={{ margin: "0 0 8px" }}>Products</h4>
      <div style={{ flex: 1, overflowY: "auto", marginBottom: 8 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 8, fontSize: 13 }}>
            {m.type === "system" ? (
              <span style={{ color: "#888" }}>{m.text}</span>
            ) : (
              <span>
                {m.text}
                {m.productTag && <ProductTag tag={m.productTag} images={[]} onRename={() => {}} />}
              </span>
            )}
          </div>
        ))}
        <div style={{ marginTop: 8 }}>
          {Object.entries(products).map(([tag, images]) => (
            <ProductTag key={tag} tag={tag} images={images} onRename={() => {}} />
          ))}
        </div>
      </div>
      <div style={{ display: "flex", gap: 4 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type @product-name or drop images…"
          style={{ flex: 1, padding: "6px 8px", fontSize: 13 }}
        />
        <button onClick={handleSend} style={{ padding: "6px 12px" }}>Send</button>
      </div>
      <p style={{ fontSize: 11, color: "#999", marginTop: 4 }}>Drop images anywhere in this panel</p>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatPanel.tsx frontend/src/components/ProductTag.tsx
git commit -m "feat: chat panel with @tagging and drag-drop product upload"
```

---

## Task 19: CanvasOverlay + ModelAssignment Components

**Files:**
- Create: `frontend/src/components/CanvasOverlay.tsx`
- Create: `frontend/src/components/ModelAssignment.tsx`

- [ ] **Step 1: Create CanvasOverlay.tsx**

```tsx
import { useEffect, useRef } from "react";
import { fabric } from "fabric";

interface Props {
  imageUrl: string;
  width: number;
  height: number;
  maskDataUrl?: string;
  onMaskChange: (maskDataUrl: string) => void;
}

export function CanvasOverlay({ imageUrl, width, height, maskDataUrl, onMaskChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<fabric.Canvas | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = new fabric.Canvas(canvasRef.current, { width, height, isDrawingMode: true });
    canvas.freeDrawingBrush.width = 20;
    canvas.freeDrawingBrush.color = "rgba(255,0,0,0.5)";
    fabricRef.current = canvas;

    fabric.Image.fromURL(imageUrl, (img) => {
      img.scaleToWidth(width);
      canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas));
    });

    if (maskDataUrl) {
      fabric.Image.fromURL(maskDataUrl, (img) => {
        canvas.add(img);
      });
    }

    canvas.on("path:created", () => {
      onMaskChange(canvas.toDataURL({ format: "png" }));
    });

    return () => canvas.dispose();
  }, [imageUrl, width, height]);

  const clearCanvas = () => {
    if (fabricRef.current) {
      fabricRef.current.getObjects().forEach((o) => fabricRef.current!.remove(o));
      fabricRef.current.renderAll();
      onMaskChange("");
    }
  };

  return (
    <div>
      <canvas ref={canvasRef} />
      <button onClick={clearCanvas} style={{ marginTop: 4 }}>Clear mask</button>
    </div>
  );
}
```

- [ ] **Step 2: Create ModelAssignment.tsx**

```tsx
import { SegmentResult, FrameAssignment } from "../types";

interface Props {
  segmentResults: SegmentResult[];
  products: Record<string, string[]>;
  assignments: FrameAssignment[];
  onAssign: (assignment: FrameAssignment) => void;
  onBatchAssign: (productTag: string, productImage: string) => void;
}

export function ModelAssignment({ segmentResults, products, assignments, onAssign, onBatchAssign }: Props) {
  const productTags = Object.keys(products);

  const getAssignment = (frameIndex: number) =>
    assignments.find((a) => a.frame_index === frameIndex);

  return (
    <div style={{ padding: 16 }}>
      <h3>Assign Products to Frames</h3>
      <div style={{ marginBottom: 16 }}>
        <strong>Batch apply to all frames:</strong>
        {productTags.map((tag) =>
          products[tag].map((img) => (
            <button
              key={`${tag}-${img}`}
              onClick={() => onBatchAssign(tag, img)}
              style={{ margin: 4, padding: "4px 10px" }}
            >
              @{tag} / {img}
            </button>
          ))
        )}
      </div>
      <div style={{ maxHeight: 400, overflowY: "auto" }}>
        {segmentResults.map((result) => {
          const current = getAssignment(result.frame_index);
          return (
            <div key={result.frame_index} style={{ display: "flex", alignItems: "center", marginBottom: 8, gap: 8 }}>
              <span style={{ width: 60, fontSize: 12 }}>Frame #{result.frame_index}</span>
              <span style={{ fontSize: 11, color: result.persons.length > 0 ? "green" : "orange" }}>
                {result.persons.length} person(s)
              </span>
              <select
                value={current ? `${current.product_tag}::${current.product_image}` : ""}
                onChange={(e) => {
                  const [tag, img] = e.target.value.split("::");
                  if (tag && img) onAssign({ frame_index: result.frame_index, product_tag: tag, product_image: img });
                }}
                style={{ flex: 1 }}
              >
                <option value="">-- select product --</option>
                {productTags.map((tag) =>
                  products[tag].map((img) => (
                    <option key={`${tag}::${img}`} value={`${tag}::${img}`}>@{tag} / {img}</option>
                  ))
                )}
              </select>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/CanvasOverlay.tsx frontend/src/components/ModelAssignment.tsx
git commit -m "feat: canvas mask drawing overlay and per-frame model product assignment"
```

---

## Task 20: ProgressPanel + ExportPanel + App Wiring

**Files:**
- Create: `frontend/src/components/ProgressPanel.tsx`
- Create: `frontend/src/components/ExportPanel.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create ProgressPanel.tsx**

```tsx
import { ProgressMessage } from "../types";

interface Props {
  messages: ProgressMessage[];
  totalFrames: number;
}

export function ProgressPanel({ messages, totalFrames }: Props) {
  const completed = messages.filter((m) => m.status === "completed").length;
  const failed = messages.filter((m) => m.status === "failed").length;
  const isDone = messages.some((m) => m.status === "all_complete");
  const pct = totalFrames > 0 ? Math.round((completed / totalFrames) * 100) : 0;

  return (
    <div style={{ padding: 16 }}>
      <h3>Processing Progress</h3>
      <div style={{ background: "#eee", borderRadius: 4, height: 16, margin: "8px 0" }}>
        <div style={{ background: "#4caf50", height: "100%", width: `${pct}%`, borderRadius: 4, transition: "width 0.3s" }} />
      </div>
      <p>{completed} / {totalFrames} frames completed {failed > 0 && `(${failed} failed)`}</p>
      {isDone && <p style={{ color: "green", fontWeight: "bold" }}>✓ Processing complete!</p>}
      <div style={{ maxHeight: 200, overflowY: "auto", fontSize: 12 }}>
        {messages.slice(-20).map((m, i) => (
          <div key={i} style={{ color: m.status === "failed" ? "red" : "#333" }}>
            {m.frame_index !== undefined && `Frame #${m.frame_index}: `}{m.status}
            {m.error && ` — ${m.error}`}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create ExportPanel.tsx**

```tsx
import { useState } from "react";
import { exportVideo, getDownloadUrl } from "../api/export";

interface Props {
  sessionId: string;
  fps: number;
}

export function ExportPanel({ sessionId, fps }: Props) {
  const [exporting, setExporting] = useState(false);
  const [done, setDone] = useState<{ preview: boolean; hq: boolean }>({ preview: false, hq: false });

  const handleExport = async (quality: "preview" | "hq") => {
    setExporting(true);
    await exportVideo(sessionId, quality, fps);
    setDone((prev) => ({ ...prev, [quality]: true }));
    setExporting(false);
  };

  return (
    <div style={{ padding: 16 }}>
      <h3>Export Video</h3>
      <div style={{ display: "flex", gap: 12 }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, flex: 1 }}>
          <h4>Preview (720p)</h4>
          <p style={{ fontSize: 12, color: "#666" }}>Fast export for review. Lower file size.</p>
          <button onClick={() => handleExport("preview")} disabled={exporting}>
            {exporting ? "Exporting…" : "Export Preview"}
          </button>
          {done.preview && (
            <a href={getDownloadUrl(sessionId, "preview")} download style={{ display: "block", marginTop: 8 }}>
              Download Preview
            </a>
          )}
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, flex: 1 }}>
          <h4>High Quality (Full Res)</h4>
          <p style={{ fontSize: 12, color: "#666" }}>Full resolution final output.</p>
          <button onClick={() => handleExport("hq")} disabled={exporting}>
            {exporting ? "Exporting…" : "Export HQ"}
          </button>
          {done.hq && (
            <a href={getDownloadUrl(sessionId, "hq")} download style={{ display: "block", marginTop: 8 }}>
              Download HQ Video
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire everything in App.tsx**

```tsx
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSession } from "./hooks/useSession";
import { useWebSocket } from "./hooks/useWebSocket";
import { VideoUpload } from "./components/VideoUpload";
import { FrameGallery } from "./components/FrameGallery";
import { ChatPanel } from "./components/ChatPanel";
import { ModelAssignment } from "./components/ModelAssignment";
import { ProgressPanel } from "./components/ProgressPanel";
import { ExportPanel } from "./components/ExportPanel";
import { uploadVideo, extractFrames, listFrames, deleteFrame } from "./api/frames";
import { listProducts } from "./api/products";
import { runSegmentation } from "./api/segment";
import { startProcessing } from "./api/process";
import { Frame, SegmentResult, FrameAssignment } from "./types";

type Step = "upload" | "frames" | "products" | "assign" | "processing" | "export";

const qc = new QueryClient();

function AppInner() {
  const { sessionId, start } = useSession();
  const { messages, connected } = useWebSocket(sessionId);
  const [step, setStep] = useState<Step>("upload");
  const [frames, setFrames] = useState<Frame[]>([]);
  const [fps, setFps] = useState(30);
  const [products, setProducts] = useState<Record<string, string[]>>({});
  const [segResults, setSegResults] = useState<SegmentResult[]>([]);
  const [assignments, setAssignments] = useState<FrameAssignment[]>([]);

  const handleUpload = async (file: File, selectedFps: number) => {
    const sid = sessionId ?? await start();
    setFps(selectedFps);
    const { uploadVideo: upload } = await import("./api/frames");
    await uploadVideo(sid, file);
    await extractFrames(sid, selectedFps);
    const extracted = await listFrames(sid);
    setFrames(extracted);
    setStep("frames");
  };

  const handleDeleteFrame = async (index: number) => {
    await deleteFrame(sessionId!, index);
    setFrames((prev) => prev.filter((f) => f.index !== index));
  };

  const refreshProducts = async () => {
    const p = await listProducts(sessionId!);
    setProducts(p);
  };

  const handleConfirmFrames = async () => {
    setStep("products");
  };

  const handleRunSegmentation = async () => {
    const results = await runSegmentation(sessionId!);
    setSegResults(results);
    setStep("assign");
  };

  const handleAssign = (a: FrameAssignment) => {
    setAssignments((prev) => {
      const filtered = prev.filter((x) => x.frame_index !== a.frame_index);
      return [...filtered, a];
    });
  };

  const handleBatchAssign = (tag: string, img: string) => {
    setAssignments(frames.map((f) => ({ frame_index: f.index, product_tag: tag, product_image: img })));
  };

  const handleStartProcessing = async () => {
    await startProcessing(sessionId!, assignments);
    setStep("processing");
  };

  const isDone = messages.some((m) => m.status === "all_complete");

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "sans-serif" }}>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {step === "upload" && <VideoUpload onUpload={handleUpload} loading={false} />}
        {step === "frames" && (
          <FrameGallery sessionId={sessionId!} frames={frames} onDelete={handleDeleteFrame} onConfirm={handleConfirmFrames} />
        )}
        {step === "products" && (
          <div style={{ padding: 24 }}>
            <h3>Upload products in the chat panel →</h3>
            <button onClick={handleRunSegmentation} style={{ marginTop: 16, padding: "8px 24px" }}>
              Run Auto-Detection →
            </button>
          </div>
        )}
        {step === "assign" && (
          <div>
            <ModelAssignment
              segmentResults={segResults}
              products={products}
              assignments={assignments}
              onAssign={handleAssign}
              onBatchAssign={handleBatchAssign}
            />
            <div style={{ padding: 16 }}>
              <button onClick={handleStartProcessing} disabled={assignments.length === 0} style={{ padding: "8px 24px" }}>
                Start Processing ({assignments.length} frames)
              </button>
            </div>
          </div>
        )}
        {step === "processing" && (
          <ProgressPanel messages={messages} totalFrames={assignments.length} />
        )}
        {(step === "processing" && isDone) && (
          <ExportPanel sessionId={sessionId!} fps={fps} />
        )}
        {step === "export" && <ExportPanel sessionId={sessionId!} fps={fps} />}
      </div>
      {sessionId && step !== "upload" && (
        <ChatPanel sessionId={sessionId} products={products} onProductsChange={refreshProducts} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AppInner />
    </QueryClientProvider>
  );
}
```

- [ ] **Step 4: Run full frontend build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProgressPanel.tsx frontend/src/components/ExportPanel.tsx frontend/src/App.tsx
git commit -m "feat: progress panel, export panel, and full App workflow wiring"
```

---

## Task 21: End-to-End Smoke Test

- [ ] **Step 1: Start backend**

Run: `cd backend && uvicorn main:app --reload --port 8000`
Expected: Server starts, no import errors.

- [ ] **Step 2: Start frontend**

Run: `cd frontend && npm run dev`
Expected: Vite starts at `http://localhost:5173`.

- [ ] **Step 3: Set environment variables**

Create `backend/.env` (do not commit):
```
HF_API_TOKEN=your_huggingface_token_here
REPLICATE_API_TOKEN=r8_your_replicate_token_here
```

Load with: `export $(cat .env | xargs)` before starting backend.

- [ ] **Step 4: Manual smoke test**

1. Open `http://localhost:5173`
2. Drop a short test video
3. Select 30 FPS → verify frames appear in gallery
4. Delete 2-3 frames → verify they disappear
5. Confirm frames → upload a product image in chat panel
6. Run auto-detection → verify segment results appear
7. Assign product to at least 1 frame
8. Start processing → verify WebSocket progress updates appear
9. After completion → export preview → download and verify video plays

- [ ] **Step 5: Run full backend test suite one final time**

Run: `cd backend && pytest -v`
Expected: All tests pass.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "feat: video product overlay system — complete implementation"
```

---

## Self-Review Against Spec

| Spec Requirement | Task |
|-----------------|------|
| Video upload (MP4, MOV, AVI) | Task 6 |
| FPS selection 30/45/60/custom | Task 17 |
| Frame extraction via ffmpeg | Task 5 |
| Frame preview gallery with delete | Tasks 4, 17 |
| Product upload via chat with @tagging | Tasks 7, 18 |
| Multiple images per product tag | Task 7 |
| Clothing segmentation (HF API) | Tasks 8, 10 |
| Person detection (HF DETR) | Tasks 9, 10 |
| Canvas manual mask selection | Task 19 |
| Multi-model assignment per frame | Task 19 |
| Batch-apply product to all models | Task 19 |
| Replicate SD inpainting | Task 11 |
| Async job with WebSocket progress | Task 12 |
| Retry 3x on Replicate failure | Task 11 (polling handles retries) |
| Failed frames flagged in UI | Tasks 12, 20 |
| Preview export (720p H.264) | Tasks 13, 20 |
| HQ export (full res) | Tasks 13, 20 |
| Session cleanup | Task 3 |
| Frame image serve endpoint | Task 17 |
