# Video Product Overlay System — Design Spec
**Date:** 2026-05-09  
**Status:** Approved  

---

## Overview

A web-based tool that takes a fashion/clothing video, extracts frames, lets the user replace garments on models with product images (t-shirts, joggers, shoes, top/bottom wear), and reconstructs the modified frames back into a video. Uses Stable Diffusion inpainting via Replicate API for seamless blending.

---

## Architecture

Three-tier system: Python/FastAPI backend handles all ML and video processing; React/Vite frontend handles UI, frame gallery, chat, and canvas selection; local filesystem handles temp file storage.

```
[User] → [React Frontend]
              ↕ REST + WebSocket
         [FastAPI Backend]
              ↕
    ┌─────────────────────────┐
    │  ffmpeg  │  HF API  │  Replicate API  │
    └─────────────────────────┘
              ↕
       [Local Temp Storage]
```

---

## User Workflow

### Step 1 — Video Upload & Frame Extraction
- User uploads video (MP4, MOV, AVI)
- Selects FPS: 30 / 45 / 60 or custom value
- Backend uses `ffmpeg-python` to extract frames as JPEG files
- Frontend shows extraction progress bar
- Frames stored at: `{session_id}/frames/`

### Step 2 — Frame Preview & Verification
- Scrollable numbered grid gallery of all extracted frames
- User reviews, can delete individual bad frames
- Confirms extraction to proceed to next step

### Step 3 — Product Upload via Chat
- Right-side chat panel with message input
- User drags/uploads product images into chat
- Images auto-tagged: `@product-1`, `@product-2` (user can rename)
- Multiple images per product supported (front, back, side, print variants) — grouped under one tag
- Chat history persists for session

### Step 4 — Area Detection & Model Assignment
- Backend runs `mattmdjaga/segformer_b2_clothes` (HuggingFace free API) on all frames
- Backend runs `facebook/detr-resnet-50` (HuggingFace free API) for person detection
- Frontend overlays detected garment regions on frame previews
- User can: accept auto-detected area OR draw manual selection on canvas (Fabric.js)
- Multi-model videos:
  - System auto-detects model changes frame-by-frame
  - User assigns `@product-tag` to each detected model
  - Option: batch-apply same product to all models at once

### Step 5 — Inpainting & Blending
- User triggers processing job
- Backend sends each frame to Replicate API (`stability-ai/stable-diffusion-inpainting`):
  - Input: base frame + segmentation mask + product image
  - Output: frame with product blended in
- Parallel API calls (up to Replicate rate limits)
- WebSocket pushes per-frame progress to frontend
- Preview quality frames shown as completed
- Processed frames stored at: `{session_id}/processed/`

### Step 6 — Video Export
- **Preview Export** — fast, lower resolution (720p), H.264, for review
- **High Quality Export** — full resolution, user-selectable codec, final delivery
- Output saved to user-specified local folder
- Session temp files cleaned up after export confirmed

---

## Technical Stack

| Layer | Tool | Cost |
|-------|------|------|
| Frame extraction | `ffmpeg-python` | Free |
| Clothing segmentation | HuggingFace free API — `mattmdjaga/segformer_b2_clothes` | Free |
| Person detection | HuggingFace free API — `facebook/detr-resnet-50` | Free |
| Inpainting/blending | Replicate API — `stability-ai/stable-diffusion-inpainting` | ~$0.002/frame |
| Video reconstruction | `ffmpeg-python` | Free |
| Backend | FastAPI + uvicorn + Python 3.11+ | Free |
| Frontend | React 18 + Vite + TypeScript | Free |
| Canvas selection | Fabric.js | Free |
| File uploads | react-dropzone | Free |
| API state | @tanstack/react-query | Free |
| Realtime progress | WebSockets (FastAPI native) | Free |
| Storage | Local temp files | Free |

**Estimated cost:** ~$1.00 per 15-second video at 30 FPS (450 frames × $0.002)

---

## Local Storage Structure

```
/tmp/sd-overlay/
  {session_id}/
    frames/           # raw extracted frames (JPEG)
    segments/         # segmentation masks (PNG)
    processed/        # inpainted frames (JPEG)
    output/           # final exported video files
```

Sessions cleaned up after export or after 24-hour TTL.

---

## Data Flow

```
Video file
  → ffmpeg extract frames → /frames/
  → HF segmentation API  → /segments/ (garment masks)
  → HF detection API     → model bounding boxes (in memory)
  → User assigns products via chat @tags
  → User confirms/adjusts areas on canvas
  → Replicate inpainting API (frame + mask + product image) → /processed/
  → ffmpeg reconstruct   → /output/video.mp4
```

---

## API Contracts (Key Endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/session` | Create new session |
| POST | `/api/session/{id}/upload` | Upload video |
| POST | `/api/session/{id}/extract` | Extract frames at FPS |
| GET  | `/api/session/{id}/frames` | List extracted frames |
| DELETE | `/api/session/{id}/frames/{n}` | Delete single frame |
| POST | `/api/session/{id}/products` | Upload product image |
| POST | `/api/session/{id}/segment` | Run segmentation on frames |
| POST | `/api/session/{id}/process` | Start inpainting job |
| WS   | `/ws/session/{id}/progress` | Real-time job progress |
| POST | `/api/session/{id}/export` | Export video (preview or HQ) |
| DELETE | `/api/session/{id}` | Cleanup session files |

---

## Error Handling

- HuggingFace API rate limit → queue requests, retry with backoff
- Replicate API failure → retry up to 3x, mark frame failed, continue batch
- Failed frames flagged in UI — user can re-trigger individually
- Session file corruption → validate frame count on load, prompt re-extraction

---

## Out of Scope (v1)

- GPU/local model inference (can swap in later)
- Cloud storage
- Multi-user / authentication
- Real-time preview (processing is async batch)
- Pose warping / precise body-contour fitting (approximate fit only)
- Audio preservation in output video (v2)
