from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, videos, shots, tags, decks

app = FastAPI(title="CVLR-API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(shots.router, prefix="/shots", tags=["shots"])
app.include_router(tags.router, prefix="/tags", tags=["tags"])
app.include_router(decks.router, prefix="/decks", tags=["decks"])
