from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import sessions, upload, frames, products

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
app.include_router(products.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
