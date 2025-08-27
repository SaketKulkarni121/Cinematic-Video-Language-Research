import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.db import get_db
from app.models import Base


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
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_tag():
    response = client.post("/tags/", json={"slug": "test", "name": "Test Tag"})
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test"
    assert data["name"] == "Test Tag"


def test_create_duplicate_tag():
    # Create first tag
    client.post("/tags/", json={"slug": "test", "name": "Test Tag"})
    
    # Try to create duplicate
    response = client.post("/tags/", json={"slug": "test", "name": "Another Tag"})
    assert response.status_code == 400


def test_list_tags():
    # Create some tags
    client.post("/tags/", json={"slug": "action", "name": "Action"})
    client.post("/tags/", json={"slug": "drama", "name": "Drama"})
    
    response = client.get("/tags/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


def test_update_tag():
    # Create tag
    create_response = client.post("/tags/", json={"slug": "test", "name": "Test Tag"})
    tag_id = create_response.json()["id"]
    
    # Update tag
    response = client.put(f"/tags/{tag_id}", json={"name": "Updated Tag"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Tag"


def test_get_nonexistent_tag():
    response = client.get("/tags/999")
    assert response.status_code == 404
