#!/usr/bin/env python3
"""
Simple startup script to test the application.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.main import app
    print("✓ Application imported successfully")
    
    # Test basic app properties
    print(f"✓ App title: {app.title}")
    print(f"✓ App version: {app.version}")
    print(f"✓ Number of routes: {len(app.routes)}")
    
    # List all routes
    print("\nAvailable routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print("\n✓ Application is ready to run!")
    print("Run with: uvicorn app.main:app --reload")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
