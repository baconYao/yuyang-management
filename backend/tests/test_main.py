import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """
    測試根路徑端點
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Yuyang Management API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"
    assert "api_versions" in data
    assert "v1" in data["api_versions"]


@pytest.mark.asyncio
async def test_docs_endpoint(client: AsyncClient):
    """
    測試 Scalar 文檔端點
    """
    response = await client.get("/docs")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Scalar API Reference" in response.text
    assert "api-reference" in response.text


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient):
    """
    測試 OpenAPI Schema 端點
    """
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Yuyang Management API"
    assert data["info"]["version"] == "1.0.0"
    assert "/api/v1/customers/" in data["paths"]
