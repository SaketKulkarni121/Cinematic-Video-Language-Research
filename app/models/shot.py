from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TimestampMixin


# Model representing a time segment from a video with vector embeddings
class Shot(Base, TimestampMixin):
    __tablename__ = "shots"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(BigInteger, ForeignKey("videos.id"), nullable=False)
    t_start_ms = Column(Integer, nullable=False)  # Start time in milliseconds
    t_end_ms = Column(Integer, nullable=False)    # End time in milliseconds
    thumb_url = Column(Text)                      # Thumbnail image URL
    embedding = Column("embedding", Text, nullable=True)  # Vector embedding for similarity search
    
    # Relationships to parent video and associated tags
    video = relationship("Video", back_populates="shots")
    tags = relationship("ShotTag", back_populates="shot", cascade="all, delete-orphan")
