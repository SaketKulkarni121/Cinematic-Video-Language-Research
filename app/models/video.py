from sqlalchemy import Column, BigInteger, Text
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TimestampMixin


# Model representing a video file with metadata and associated shots
class Video(Base, TimestampMixin):
    __tablename__ = "videos"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)    # Video title/name
    src_url = Column(Text, nullable=False)  # Source URL or file path
    
    # Relationship to shots extracted from this video
    shots = relationship("Shot", back_populates="video", cascade="all, delete-orphan")
