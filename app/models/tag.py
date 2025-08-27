from sqlalchemy import Column, BigInteger, Text, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TimestampMixin


# Model representing descriptive labels that can be applied to shots
class Tag(Base, TimestampMixin):
    __tablename__ = "tags"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slug = Column(Text, nullable=False, unique=True)  # Clean tag name
    name = Column(Text, nullable=False)               # Public tag name
    
    # Relationship to shots that have this tag
    shots = relationship("ShotTag", back_populates="tag", cascade="all, delete-orphan")


# Junction table linking shots to tags (many-to-many relationship)
class ShotTag(Base):
    __tablename__ = "shot_tags"
    
    shot_id = Column(BigInteger, ForeignKey("shots.id"), primary_key=True)
    tag_id = Column(BigInteger, ForeignKey("tags.id"), primary_key=True)
    
    # Relationships to associated shot and tag
    shot = relationship("Shot", back_populates="tags")
    tag = relationship("Tag", back_populates="shots")
