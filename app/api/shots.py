from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.pagination import PaginationParams, PaginatedResponse, get_offset, get_total_pages
from app.models.shot import Shot
from app.models.video import Video
from app.models.tag import Tag, ShotTag
from app.search.embedder import get_embedder
from app.search.queries import build_shot_query, build_vector_query, get_similar_shots
from pydantic import BaseModel


class ShotResponse(BaseModel):
    id: int
    video_id: int
    t_start_ms: int
    t_end_ms: int
    thumb_url: Optional[str]
    video_title: str
    tags: List[str]

    class Config:
        from_attributes = True


class ShotDetailResponse(BaseModel):
    id: int
    video_id: int
    t_start_ms: int
    t_end_ms: int
    thumb_url: Optional[str]
    video_title: str
    video_src_url: str
    tags: List[str]
    similar_shots: List[ShotResponse]

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ShotResponse])
async def list_shots(
    q: Optional[str] = Query(None, description="Text query for vector search"),
    top_k: int = Query(200, ge=1, le=1000, description="Vector search limit"),
    tag_slugs: Optional[List[str]] = Query(None, description="Filter by tag slugs"),
    tag_query: Optional[str] = Query(None, description="Fuzzy tag search"),
    threshold: float = Query(0.2, ge=0.0, le=1.0, description="Tag similarity threshold"),
    hybrid: bool = Query(True, description="Intersect vector and tag results"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(24, ge=1, le=60, description="Items per page")
):
    db = next(get_db())
    
    if q:
        embedder = get_embedder()
        query_vector = embedder.embed(q)
        
        if query_vector:
            shot_ids = build_vector_query(
                db, query_vector, top_k, tag_slugs, tag_query, threshold, hybrid
            )
            
            if shot_ids:
                # Apply pagination to vector search results
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_ids = shot_ids[start_idx:end_idx]
                
                shots = db.query(Shot).filter(Shot.id.in_(paginated_ids)).all()
                # Reorder by original order from vector search
                shot_dict = {s.id: s for s in shots}
                shots = [shot_dict[sid] for sid in paginated_ids if sid in shot_dict]
                total = len(shot_ids)  # Total available from vector search
            else:
                shots = []
                total = 0
        else:
            shots = []
            total = 0
    else:
        query, total = build_shot_query(
            db, tag_slugs, tag_query, threshold, page, page_size
        )
        shots = query.all()
    
    # Get video and tag info for each shot
    shot_responses = []
    for shot in shots:
        video = db.query(Video).filter(Video.id == shot.video_id).first()
        tags = db.query(Tag).join(ShotTag).filter(ShotTag.shot_id == shot.id).all()
        
        shot_responses.append(ShotResponse(
            id=shot.id,
            video_id=shot.video_id,
            t_start_ms=shot.t_start_ms,
            t_end_ms=shot.t_end_ms,
            thumb_url=shot.thumb_url,
            video_title=video.title if video else "",
            tags=[tag.name for tag in tags]
        ))
    
    return PaginatedResponse(
        items=shot_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=get_total_pages(total, page_size)
    )


@router.get("/{shot_id}", response_model=ShotDetailResponse)
async def get_shot(shot_id: int, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    
    video = db.query(Video).filter(Video.id == shot.video_id).first()
    tags = db.query(Tag).join(ShotTag).filter(ShotTag.shot_id == shot.id).all()
    
    similar_shots = []
    if shot.embedding:
        similar_shots_data = get_similar_shots(db, shot_id, 5)
        for similar_shot in similar_shots_data:
            similar_video = db.query(Video).filter(Video.id == similar_shot.video_id).first()
            similar_tags = db.query(Tag).join(ShotTag).filter(ShotTag.shot_id == similar_shot.id).all()
            
            similar_shots.append(ShotResponse(
                id=similar_shot.id,
                video_id=similar_shot.video_id,
                t_start_ms=similar_shot.t_start_ms,
                t_end_ms=similar_shot.t_end_ms,
                thumb_url=similar_shot.thumb_url,
                video_title=similar_video.title if similar_video else "",
                tags=[tag.name for tag in similar_tags]
            ))
    
    return ShotDetailResponse(
        id=shot.id,
        video_id=shot.video_id,
        t_start_ms=shot.t_start_ms,
        t_end_ms=shot.t_end_ms,
        thumb_url=shot.thumb_url,
        video_title=video.title if video else "",
        video_src_url=video.src_url if video else "",
        tags=[tag.name for tag in tags],
        similar_shots=similar_shots
    )
