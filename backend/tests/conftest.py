import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """
    創建 FastAPI 測試客戶端
    """
    return TestClient(app)
