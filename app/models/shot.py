from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TimestampMixin


class Shot(Base, TimestampMixin):
    __tablename__ = "shots"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(BigInteger, ForeignKey("videos.id"), nullable=False)
    t_start_ms = Column(Integer, nullable=False)
    t_end_ms = Column(Integer, nullable=False)
    thumb_url = Column(Text)
    embedding = Column("embedding", Text, nullable=True)  # Will be cast to VECTOR in migration
    
    video = relationship("Video", back_populates="shots")
    tags = relationship("ShotTag", back_populates="shot", cascade="all, delete-orphan")
