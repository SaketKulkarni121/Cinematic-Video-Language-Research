from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.video import Video
from app.models.shot import Shot
from pydantic import BaseModel


class VideoCreate(BaseModel):
    title: str
    src_url: str


class VideoResponse(BaseModel):
    id: int
    title: str
    src_url: str
    shot_count: int

    class Config:
        from_attributes = True


router = APIRouter()


@router.post("/", response_model=VideoResponse)
async def create_video(video: VideoCreate, db: Session = Depends(get_db)):
    db_video = Video(title=video.title, src_url=video.src_url)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    shot_count = db.query(Shot).filter(Shot.video_id == db_video.id).count()
    
    return VideoResponse(
        id=db_video.id,
        title=db_video.title,
        src_url=db_video.src_url,
        shot_count=shot_count
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    shot_count = db.query(Shot).filter(Shot.video_id == video_id).count()
    
    return VideoResponse(
        id=video.id,
        title=video.title,
        src_url=video.src_url,
        shot_count=shot_count
    )
