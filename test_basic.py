#!/usr/bin/env python3
"""
Basic test script to verify the application works.
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from app.main import app
from fastapi.testclient import TestClient

def test_health():
    """Test the health endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    print("✓ Health endpoint works")

def test_app_structure():
    """Test that the app has the expected structure."""
    assert hasattr(app, 'routes'), "App should have routes"
    print("✓ App structure is correct")

if __name__ == "__main__":
    print("Running basic tests...")
    test_app_structure()
    test_health()
    print("All basic tests passed!")
