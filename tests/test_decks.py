import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.db import get_db
from app.models import Base, Video, Shot


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    try:
        video = Video(title="Test Video", src_url="https://example.com/test.mp4")
        db.add(video)
        db.commit()
        db.refresh(video)
        
        shot = Shot(
            video_id=video.id,
            t_start_ms=0,
            t_end_ms=5000,
            thumb_url="https://example.com/thumb.jpg"
        )
        db.add(shot)
        db.commit()
        db.refresh(shot)
    finally:
        db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_deck():
    response = client.post("/decks/", json={"user_id": 1, "title": "Test Deck"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Deck"
    assert data["user_id"] == 1


def test_list_decks():
    # Create a deck
    client.post("/decks/", json={"user_id": 1, "title": "Test Deck"})
    
    response = client.get("/decks/?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Deck"


def test_add_deck_item():
    # Create deck
    deck_response = client.post("/decks/", json={"user_id": 1, "title": "Test Deck"})
    deck_id = deck_response.json()["id"]
    
    # Add shot to deck
    response = client.post(f"/decks/{deck_id}/items", json={"shot_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["shot_id"] == 1


def test_remove_deck_item():
    # Create deck and add item
    deck_response = client.post("/decks/", json={"user_id": 1, "title": "Test Deck"})
    deck_id = deck_response.json()["id"]
    
    client.post(f"/decks/{deck_id}/items", json={"shot_id": 1})
    
    # Remove item
    response = client.delete(f"/decks/{deck_id}/items/1")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_reorder_deck_items():
    # Create deck and add items
    deck_response = client.post("/decks/", json={"user_id": 1, "title": "Test Deck"})
    deck_id = deck_response.json()["id"]
    
    client.post(f"/decks/{deck_id}/items", json={"shot_id": 1, "sort_order": 0})
    
    # Reorder items
    response = client.put(f"/decks/{deck_id}/items/reorder", json={
        "items": [{"shot_id": 1, "sort_order": 5}]
    })
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_get_deck_detail():
    # Create deck and add item
    deck_response = client.post("/decks/", json={"user_id": 1, "title": "Test Deck"})
    deck_id = deck_response.json()["id"]
    
    client.post(f"/decks/{deck_id}/items", json={"shot_id": 1})
    
    # Get deck detail
    response = client.get(f"/decks/{deck_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Deck"
    assert len(data["items"]) == 1
