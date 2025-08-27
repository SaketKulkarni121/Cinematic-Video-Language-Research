#!/usr/bin/env python3
"""
Seed script for CVLR backend.
Inserts sample data for development and testing.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.db import SessionLocal, engine
from app.models import Base, Video, Shot, Tag, ShotTag, Deck, DeckItem
from app.search.embedder import get_embedder


def seed_database():
    """Seed the database with sample data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Video).first():
            print("Database already seeded. Skipping...")
            return
        
        print("Seeding database...")
        
        # Create sample video
        video = Video(
            title="Sample Cinematic Video",
            src_url="https://example.com/sample-video.mp4"
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Create sample tags
        tags = [
            Tag(slug="action", name="Action"),
            Tag(slug="drama", name="Drama"),
            Tag(slug="cinematic", name="Cinematic"),
            Tag(slug="closeup", name="Close-up"),
            Tag(slug="wide", name="Wide Shot")
        ]
        
        for tag in tags:
            db.add(tag)
        db.commit()
        
        # Create sample shots
        shots = [
            Shot(
                video_id=video.id,
                t_start_ms=0,
                t_end_ms=5000,
                thumb_url="https://example.com/thumb1.jpg",
                embedding=None
            ),
            Shot(
                video_id=video.id,
                t_start_ms=5000,
                t_end_ms=10000,
                thumb_url="https://example.com/thumb2.jpg",
                embedding=None
            ),
            Shot(
                video_id=video.id,
                t_start_ms=10000,
                t_end_ms=15000,
                thumb_url="https://example.com/thumb3.jpg",
                embedding=None
            ),
            Shot(
                video_id=video.id,
                t_start_ms=15000,
                t_end_ms=20000,
                thumb_url="https://example.com/thumb4.jpg",
                embedding=None
            )
        ]
        
        for shot in shots:
            db.add(shot)
        db.commit()
        
        # Link shots to tags
        shot_tags = [
            ShotTag(shot_id=shots[0].id, tag_id=tags[0].id),  # Action
            ShotTag(shot_id=shots[0].id, tag_id=tags[2].id),  # Cinematic
            ShotTag(shot_id=shots[1].id, tag_id=tags[1].id),  # Drama
            ShotTag(shot_id=shots[1].id, tag_id=tags[3].id),  # Close-up
            ShotTag(shot_id=shots[2].id, tag_id=tags[2].id),  # Cinematic
            ShotTag(shot_id=shots[2].id, tag_id=tags[4].id),  # Wide Shot
            ShotTag(shot_id=shots[3].id, tag_id=tags[0].id),  # Action
            ShotTag(shot_id=shots[3].id, tag_id=tags[2].id),  # Cinematic
        ]
        
        for shot_tag in shot_tags:
            db.add(shot_tag)
        db.commit()
        
        # Create sample deck
        deck = Deck(
            user_id=1,
            title="My Favorite Shots"
        )
        db.add(deck)
        db.commit()
        
        # Add shots to deck
        deck_items = [
            DeckItem(deck_id=deck.id, shot_id=shots[0].id, sort_order=0),
            DeckItem(deck_id=deck.id, shot_id=shots[2].id, sort_order=1),
        ]
        
        for item in deck_items:
            db.add(item)
        db.commit()
        
        print("Database seeded successfully!")
        print(f"- Created 1 video: {video.title}")
        print(f"- Created {len(shots)} shots")
        print(f"- Created {len(tags)} tags")
        print(f"- Created 1 deck: {deck.title}")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
