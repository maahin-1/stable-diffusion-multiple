# Video Product Overlay: virtual try-on for video with Stable Diffusion inpainting

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=black)

**Video Product Overlay is an open-source web app that replaces the clothing on people in a video with product images you upload, frame by frame.** It splits a video into frames, finds each person's clothing with a SegFormer segmentation model, swaps in your product (a t-shirt, dress or jacket tagged with `@name`) using Stable Diffusion inpainting, and stitches the frames back into a preview or full-quality video. A React wizard drives the FastAPI backend, and inpainting progress streams live over WebSocket.

Use it for virtual try-on demos, fashion and e-commerce video mockups, or experiments with video inpainting. The models run on hosted APIs (Hugging Face and Replicate), so no local GPU is needed.

---

## Contents

- [What this project does](#what-this-project-does)
- [How it works (pipeline)](#how-it-works-pipeline)
- [Architecture](#architecture)
- [Storage layout](#storage-layout)
- [Setup](#setup)
- [API surface (REST)](#api-surface-rest)
- [Why this approach](#why-this-approach)
- [Limits / known constraints](#limits--known-constraints)
- [Tech stack](#tech-stack)
- [FAQ](#faq)
- [License](#license)

---
## What this project does

Given a short video containing one or more people, this app lets you:

1. Upload product images (e.g. a t-shirt, dress, jacket).
2. Tag each product with an `@name` (e.g. `@redshirt`, `@blacktee`).
3. Automatically detect the clothing regions on every person in every frame.
4. Replace the clothing in those regions with your product image using Stable Diffusion inpainting.
5. Stitch the modified frames back into a final video — preview (720p) or HQ.

The end result: a video where the people are now "wearing" the products you uploaded, without any manual editing.

## How it works (pipeline)

```
[Video] → [Frames] → [Segment clothing + detect people] → [Assign product per frame] → [Inpaint] → [Reconstruct video]
```

Every step is session-scoped — each upload gets its own working directory under `SD_STORAGE/{session_id}/` so multiple jobs don't clobber each other.

### Step-by-step

| # | Step | What happens | Service / Model |
|---|---|---|---|
| 1 | **Session start** | New UUID, empty workspace created | local filesystem |
| 2 | **Video upload** | MP4/MOV/AVI saved as `video.mp4` | FastAPI multipart |
| 3 | **Frame extraction** | Video split into JPEG frames at chosen FPS | `ffmpeg` (system binary) via `ffmpeg-python` |
| 4 | **Product upload** | Image dropped into chat panel, tagged with `@name` | local filesystem under `products/{tag}/` |
| 5 | **Segmentation** | Per-frame: clothing mask + person bounding boxes | HuggingFace Inference API — `mattmdjaga/segformer_b2_clothes` + `facebook/detr-resnet-50` |
| 6 | **Assignment** | UI lets you pick which product goes on which frame (or batch-apply one to all) | React state |
| 7 | **Inpainting** | For each frame: send (frame, mask, product image) to inpainting model, save result | Replicate API — Stable Diffusion inpainting |
| 8 | **Video reconstruction** | Processed JPEGs reassembled into MP4 | `ffmpeg` (preview = 720p/CRF28, HQ = original res/CRF18) |

Progress for the long-running step (inpainting) streams over **WebSocket** so the UI updates per-frame instead of waiting on a single HTTP response.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite, port 5173)                         │
│  - 7-step wizard: start → upload → frames → products →      │
│    assign → process → export                                │
│  - Chat panel for product image upload (drag-drop + @tag)   │
│  - Axios for REST, native WebSocket for progress            │
└────────────────────┬────────────────────────────────────────┘
                     │  HTTP (REST)  +  WebSocket (progress)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + uvicorn, port 8000)                     │
│  Routers: sessions, upload, frames, products, segment,      │
│           process, ws, export                               │
│  Services: video, segmentation, detection, inpainting,      │
│            job_runner                                       │
│  Storage: session_store, frame_store (filesystem-backed)    │
└──────┬────────────┬────────────┬────────────────────────────┘
       │            │            │
       ▼            ▼            ▼
   ffmpeg     HuggingFace    Replicate API
  (local)     Inference API   (Stable Diffusion
                              inpainting)
```

### Backend layout

- `main.py` — FastAPI app, loads `.env`, mounts all routers.
- `config.py` — env-driven config (`BASE_STORAGE`, `REPLICATE_API_TOKEN`, `HF_API_TOKEN`, FPS bounds).
- `routers/` — one file per resource group (sessions, frames, products, segment, process, export, ws).
- `services/` — pure business logic:
  - `video.py` — `extract_frames`, `reconstruct_video` (ffmpeg wrappers).
  - `segmentation.py` — calls HF segmentation, decodes per-label base64 masks, ORs clothing labels into one mask.
  - `detection.py` — calls HF DETR, filters for `person` label.
  - `inpainting.py` — calls Replicate, returns processed frame.
  - `job_runner.py` — async loop over assignments, calls inpainting, emits WebSocket progress events.
- `storage/` — filesystem helpers (no DB; everything is files under `SD_STORAGE/{session_id}/`).

### Frontend layout

- `App.tsx` — single-page wizard, step state machine.
- `hooks/useSession.ts` — wraps all API calls; holds session, frames, products, segments.
- `hooks/useWebSocket.ts` — subscribes to per-session progress channel.
- `api/*` — thin axios wrappers, one per backend resource.
- `components/` — `VideoUpload`, `FrameGallery`, `FrameCard`, `ChatPanel`, `ProductTag`, `CanvasOverlay` (Fabric.js), `ModelAssignment`, `ProgressPanel`, `ExportPanel`.

## Storage layout

```
SD_STORAGE/                          # ./sd-overlay by default
└── {session_id}/
    ├── video.mp4                    # uploaded source
    ├── frames/
    │   └── frame_00001.jpg ...      # extracted at chosen FPS
    ├── products/
    │   ├── {tag}/                   # one dir per @tag
    │   │   └── image.png
    │   └── index.json
    ├── segments/
    │   └── mask_00001.png ...       # clothing masks (one per frame)
    ├── processed/
    │   └── frame_00001.jpg ...      # inpainted output
    └── exports/
        ├── preview.mp4
        └── hq.mp4
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- `ffmpeg` on `PATH` (download from [ffmpeg.org](https://ffmpeg.org/download.html))
- HuggingFace API token (free) — for segmentation & person detection
- Replicate API token (paid, ~$0.01/image) — for SD inpainting

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```
REPLICATE_API_TOKEN=r8_...
HF_API_TOKEN=hf_...
SD_STORAGE=D:/projects for fun/stable-diffusion/sd-overlay
```

Run:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## API surface (REST)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/session` | Create new session |
| `DELETE` | `/api/session/{id}` | Delete session + all its files |
| `POST` | `/api/session/{id}/upload` | Upload `video.mp4` |
| `POST` | `/api/session/{id}/extract` | Extract frames at given FPS |
| `GET` | `/api/session/{id}/frames` | List extracted frames |
| `DELETE` | `/api/session/{id}/frames/{index}` | Remove a single frame |
| `GET` | `/api/session/{id}/frames/{filename}/image` | Serve frame JPEG |
| `POST` | `/api/session/{id}/products` | Upload product image with `@tag` |
| `GET` | `/api/session/{id}/products` | List products |
| `GET` | `/api/session/{id}/products/{tag}/{filename}/image` | Serve product image |
| `POST` | `/api/session/{id}/segment` | Run segmentation + person detection on all frames |
| `POST` | `/api/session/{id}/process` | Start inpainting job (returns immediately) |
| `WS` | `/ws/session/{id}/progress` | Stream per-frame inpainting progress |
| `POST` | `/api/session/{id}/export` | Reconstruct video (`mode=preview` or `mode=hq`) |

## Why this approach

- **Filesystem storage, no DB** — each session is fully self-contained, easy to inspect/debug, easy to delete.
- **Hosted models, not local** — running SD locally needs a GPU; offloading to Replicate keeps the app runnable on any laptop. HF Inference API gives free-tier segmentation/detection.
- **Sync REST for fast ops, WebSocket for the slow one** — frame extraction, segmentation, and listing return immediately. Inpainting is the only step that can take minutes, so it runs as a background task and pushes progress over WebSocket.
- **Per-frame product assignment** — same product can apply to all frames (batch), or you can vary it per frame for outfit changes mid-video.

## Limits / known constraints

- Segmentation accuracy depends on `segformer_b2_clothes` — works best on full-body shots with simple backgrounds.
- HF free tier may cold-start models (first call slow, ~20s) and rate-limits aggressively.
- Inpainting cost scales linearly with frame count × $0.01-ish per frame (Replicate pricing).
- Tested on Windows 11 / Python 3.12 / Node 22.

## Tech stack

**Backend:** FastAPI, uvicorn, ffmpeg-python, Pillow, numpy, requests, python-dotenv, python-multipart
**Frontend:** React 18, Vite 8, TypeScript, axios, @tanstack/react-query, react-dropzone, fabric.js
**Models:** Stable Diffusion inpainting (Replicate), SegFormer B2 clothes (HF), DETR ResNet-50 (HF)

---

## FAQ

### What is Video Product Overlay?
A FastAPI and React app that performs virtual try-on on video: it detects clothing on every person in every frame and replaces it with your uploaded product image using Stable Diffusion inpainting.

### Do I need a GPU?
No. Segmentation uses the Hugging Face Inference API and inpainting uses Replicate, so the app runs on an ordinary laptop.

### What does it cost to run?
Hugging Face's free tier covers segmentation and person detection. Replicate inpainting costs about $0.01 per frame, so cost grows linearly with frame count.

### Which models does it use?
SegFormer B2 clothes (`mattmdjaga/segformer_b2_clothes`) for clothing masks, DETR ResNet-50 for person detection, and Stable Diffusion inpainting on Replicate.

### What are the known limits?
Segmentation works best on full-body shots with simple backgrounds, the free Hugging Face tier can cold-start slowly, and it has only been tested on Windows 11 with Python 3.12 and Node 22.

### Which video formats work?
MP4, MOV and AVI uploads. Export is a 720p preview or a full-resolution HQ render through ffmpeg.

## License

MIT. See [LICENSE](LICENSE).
