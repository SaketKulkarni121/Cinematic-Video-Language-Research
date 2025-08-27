from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db
from app.models.deck import Deck, DeckItem
from app.models.shot import Shot
from app.models.video import Video
from app.models.tag import Tag, ShotTag
from pydantic import BaseModel


class DeckCreate(BaseModel):
    user_id: int
    title: str


class DeckResponse(BaseModel):
    id: int
    user_id: int
    title: str

    class Config:
        from_attributes = True


class DeckItemCreate(BaseModel):
    shot_id: int
    sort_order: Optional[int] = None


class DeckItemResponse(BaseModel):
    shot_id: int
    sort_order: int
    shot_title: str
    video_title: str
    tags: List[str]

    class Config:
        from_attributes = True


class DeckDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    items: List[DeckItemResponse]

    class Config:
        from_attributes = True


class ReorderRequest(BaseModel):
    items: List[dict]


router = APIRouter()


@router.get("/", response_model=List[DeckResponse])
async def list_decks(user_id: int, db: Session = Depends(get_db)):
    decks = db.query(Deck).filter(Deck.user_id == user_id).all()
    return [DeckResponse.from_orm(deck) for deck in decks]


@router.post("/", response_model=DeckResponse)
async def create_deck(deck: DeckCreate, db: Session = Depends(get_db)):
    db_deck = Deck(user_id=deck.user_id, title=deck.title)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    
    return DeckResponse.from_orm(db_deck)


@router.get("/{deck_id}", response_model=DeckDetailResponse)
async def get_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    items = db.query(DeckItem).filter(DeckItem.deck_id == deck_id).order_by(DeckItem.sort_order).all()
    
    item_responses = []
    for item in items:
        shot = db.query(Shot).filter(Shot.id == item.shot_id).first()
        if shot:
            video = db.query(Video).filter(Video.id == shot.video_id).first()
            tags = db.query(Tag).join(ShotTag).filter(ShotTag.shot_id == shot.id).all()
            
            item_responses.append(DeckItemResponse(
                shot_id=item.shot_id,
                sort_order=item.sort_order,
                shot_title=f"{shot.t_start_ms}ms - {shot.t_end_ms}ms",
                video_title=video.title if video else "",
                tags=[tag.name for tag in tags]
            ))
    
    return DeckDetailResponse(
        id=deck.id,
        user_id=deck.user_id,
        title=deck.title,
        items=item_responses
    )


@router.post("/{deck_id}/items", response_model=DeckItemResponse)
async def add_deck_item(deck_id: int, item: DeckItemCreate, db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    shot = db.query(Shot).filter(Shot.id == item.shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    
    existing = db.query(DeckItem).filter(
        DeckItem.deck_id == deck_id, DeckItem.shot_id == item.shot_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Shot already in deck")
    
    if item.sort_order is None:
        max_order = db.query(DeckItem).filter(DeckItem.deck_id == deck_id).with_entities(
            func.max(DeckItem.sort_order)
        ).scalar() or 0
        item.sort_order = max_order + 1
    
    db_item = DeckItem(deck_id=deck_id, shot_id=item.shot_id, sort_order=item.sort_order)
    db.add(db_item)
    db.commit()
    
    video = db.query(Video).filter(Video.id == shot.video_id).first()
    tags = db.query(Tag).join(ShotTag).filter(ShotTag.shot_id == shot.id).all()
    
    return DeckItemResponse(
        shot_id=item.shot_id,
        sort_order=item.sort_order,
        shot_title=f"{shot.t_start_ms}ms - {shot.t_end_ms}ms",
        video_title=video.title if video else "",
        tags=[tag.name for tag in tags]
    )


@router.delete("/{deck_id}/items/{shot_id}")
async def remove_deck_item(deck_id: int, shot_id: int, db: Session = Depends(get_db)):
    item = db.query(DeckItem).filter(
        DeckItem.deck_id == deck_id, DeckItem.shot_id == shot_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Deck item not found")
    
    db.delete(item)
    db.commit()
    
    return {"ok": True}


@router.put("/{deck_id}/items/reorder")
async def reorder_deck_items(deck_id: int, request: ReorderRequest, db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    for item_data in request.items:
        shot_id = item_data.get("shot_id")
        sort_order = item_data.get("sort_order")
        
        if shot_id is None or sort_order is None:
            raise HTTPException(status_code=400, detail="Invalid item data")
        
        item = db.query(DeckItem).filter(
            DeckItem.deck_id == deck_id, DeckItem.shot_id == shot_id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Shot {shot_id} not found in deck")
        
        item.sort_order = sort_order
    
    db.commit()
    return {"ok": True}
