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
