from typing import List, Optional, Tuple
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models.shot import Shot
from app.models.tag import Tag, ShotTag
from app.models.video import Video


def build_shot_query(
    db: Session,
    tag_slugs: Optional[List[str]] = None,
    tag_query: Optional[str] = None,
    threshold: float = 0.2,
    page: int = 1,
    page_size: int = 24
) -> Tuple[Select, int]:
    query = db.query(Shot).join(Video)
    
    if tag_slugs:
        query = query.join(ShotTag).join(Tag).filter(Tag.slug.in_(tag_slugs))
    
    if tag_query:
        query = query.join(ShotTag).join(Tag).filter(
            func.similarity(Tag.name, tag_query) >= threshold
        ).order_by(func.similarity(Tag.name, tag_query).desc())
    
    total = query.count()
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    return query, total


def build_vector_query(
    db: Session,
    query_vector: List[float],
    top_k: int = 200,
    tag_slugs: Optional[List[str]] = None,
    tag_query: Optional[str] = None,
    threshold: float = 0.2,
    hybrid: bool = True
) -> List[int]:
    if not query_vector:
        return []
    
    vector_str = f"[{','.join(map(str, query_vector))}]"
    
    if hybrid and (tag_slugs or tag_query):
        tag_query, _ = build_shot_query(db, tag_slugs, tag_query, threshold, 1, 10000)
        tag_shot_ids = [s.id for s in tag_query.all()]
        
        if not tag_shot_ids:
            return []
        
        vector_query = text(f"""
            SELECT id FROM shots 
            WHERE id = ANY(:shot_ids) AND embedding IS NOT NULL
            ORDER BY embedding <-> :query_vector
            LIMIT :top_k
        """)
        
        result = db.execute(vector_query, {
            "shot_ids": tag_shot_ids,
            "query_vector": vector_str,
            "top_k": top_k
        })
        
        return [row[0] for row in result]
    else:
        vector_query = text(f"""
            SELECT id FROM shots 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> :query_vector
            LIMIT :top_k
        """)
        
        result = db.execute(vector_query, {
            "query_vector": vector_str,
            "top_k": top_k
        })
        
        return [row[0] for row in result]


def get_similar_shots(db: Session, shot_id: int, limit: int = 5) -> List[Shot]:
    query = text(f"""
        SELECT s2.* FROM shots s1
        JOIN shots s2 ON s1.embedding IS NOT NULL AND s2.embedding IS NOT NULL
        WHERE s1.id = :shot_id AND s2.id != :shot_id
        ORDER BY s1.embedding <-> s2.embedding
        LIMIT :limit
    """)
    
    result = db.execute(query, {"shot_id": shot_id, "limit": limit})
    return [Shot(**dict(row._mapping)) for row in result]
