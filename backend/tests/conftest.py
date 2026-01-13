"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture(scope="session")
def data_loader():
    """Session-scoped DataLoader with real parquet data."""
    from app.services.data_loader import DataLoader
    return DataLoader()


@pytest.fixture(scope="session")
def client():
    """Session-scoped test client."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_teacher_id(data_loader):
    """Return a valid teacher_id from filtered data."""
    return int(data_loader.scores_df['teacher_id'].iloc[0])


@pytest.fixture
def sample_student_id(data_loader):
    """Return a valid student_id from filtered data."""
    return int(data_loader.scores_df['student_id'].iloc[0])


@pytest.fixture
def sample_class_id(data_loader):
    """Return a valid class_id from filtered data."""
    return int(data_loader.scores_df['class_id'].iloc[0])


@pytest.fixture
def sample_subject(data_loader):
    """Return a valid subject from filtered data."""
    return str(data_loader.scores_df['discipline_name'].iloc[0])


@pytest.fixture
def valid_teacher_class_subject(data_loader):
    """Return a valid (teacher_id, class_id, subject) combination."""
    row = data_loader.scores_df.iloc[0]
    return (
        int(row['teacher_id']),
        int(row['class_id']),
        str(row['discipline_name'])
    )
