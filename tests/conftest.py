"""
Pytest configuration for SME Interview System tests.
"""

import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    """Mock configuration for all tests."""
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
    monkeypatch.setenv('GOOGLE_API_KEY', 'test-google-key')
    monkeypatch.setenv('DATABASE_PATH', ':memory:')
    monkeypatch.setenv('FLASK_ENV', 'testing')
