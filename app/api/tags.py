from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db
from app.core.pagination import PaginationParams, PaginatedResponse, get_offset, get_total_pages
from app.models.tag import Tag
from pydantic import BaseModel


# Data models for tag operations
class TagCreate(BaseModel):
    slug: str
    name: str


class TagUpdate(BaseModel):
    slug: Optional[str] = None
    name: Optional[str] = None


class TagResponse(BaseModel):
    id: int
    slug: str
    name: str

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TagResponse])
async def list_tags(
    query: Optional[str] = Query(None, description="Fuzzy search query"),
    threshold: float = Query(0.2, ge=0.0, le=1.0, description="Similarity threshold"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(24, ge=1, le=60, description="Items per page")
):
    """List tags with optional fuzzy search and pagination"""
    db = next(get_db())
    
    tag_query = db.query(Tag)
    
    if query:
        # Apply fuzzy search using PostgreSQL similarity function
        tag_query = tag_query.filter(
            func.similarity(Tag.name, query) >= threshold
        ).order_by(func.similarity(Tag.name, query).desc())
    
    total = tag_query.count()
    tags = tag_query.offset(get_offset(page, page_size)).limit(page_size).all()
    
    return PaginatedResponse(
        items=[TagResponse.from_orm(tag) for tag in tags],
        total=total,
        page=page,
        page_size=page_size,
        pages=get_total_pages(total, page_size)
    )


@router.post("/", response_model=TagResponse)
async def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    """Create a new tag"""
    # Check for duplicate slug
    existing = db.query(Tag).filter(Tag.slug == tag.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this slug already exists")
    
    db_tag = Tag(slug=tag.slug, name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return TagResponse.from_orm(db_tag)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: int, tag_update: TagUpdate, db: Session = Depends(get_db)):
    """Update an existing tag"""
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Update slug if provided, checking for conflicts
    if tag_update.slug is not None:
        existing = db.query(Tag).filter(Tag.slug == tag_update.slug, Tag.id != tag_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Tag with this slug already exists")
        db_tag.slug = tag_update.slug
    
    # Update name if provided
    if tag_update.name is not None:
        db_tag.name = tag_update.name
    
    db.commit()
    db.refresh(db_tag)
    
    return TagResponse.from_orm(db_tag)
