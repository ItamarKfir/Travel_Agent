"""
Tests package initialization.

This file ensures the backend directory is in the Python path
when tests are run directly.
"""
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

