from sqlalchemy import Column, BigInteger, Text
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TimestampMixin


class Video(Base, TimestampMixin):
    __tablename__ = "videos"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    src_url = Column(Text, nullable=False)
    
    shots = relationship("Shot", back_populates="video", cascade="all, delete-orphan")
