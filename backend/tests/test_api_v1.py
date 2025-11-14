from fastapi.testclient import TestClient


def test_hello_endpoint(client: TestClient):
    """
    測試 Hello World 端點
    """
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello, World!"
    assert data["status"] == "success"
    assert data["version"] == "v1"
