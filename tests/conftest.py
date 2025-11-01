"""Pytest configuration for Inscenium tests."""

import os
import pytest
from pathlib import Path

# Set test environment variables
os.environ["MOCK_ML_MODELS"] = "true"
os.environ["INSCENIUM_TEST_MODE"] = "true"
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)

@pytest.fixture
def mock_video_path():
    """Mock video path for testing."""
    return "tests/golden_scenes/assets/sample.mp4"

@pytest.fixture
def test_database_url():
    """Test database URL."""
    return os.getenv("TEST_DATABASE_URL", "postgresql://inscenium:inscenium@localhost:5432/inscenium_test")