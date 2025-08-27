from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base
from app.models.base import TimestampMixin


# Model representing a collection of shots created by a user
class Deck(Base, TimestampMixin):
    __tablename__ = "decks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    title = Column(Text, nullable=False)
    
    # Relationship to deck items (shots in this deck)
    items = relationship("DeckItem", back_populates="deck", cascade="all, delete-orphan")


# Junction table linking shots to decks with ordering information
class DeckItem(Base):
    __tablename__ = "deck_items"
    
    deck_id = Column(BigInteger, ForeignKey("decks.id", ondelete="CASCADE"), primary_key=True)
    shot_id = Column(BigInteger, ForeignKey("shots.id", ondelete="CASCADE"), primary_key=True)
    sort_order = Column(Integer, default=0)  # Order of shots within the deck
    
    # Relationships to parent deck and associated shot
    deck = relationship("Deck", back_populates="items")
    shot = relationship("Shot")
