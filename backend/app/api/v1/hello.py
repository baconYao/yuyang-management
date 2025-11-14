from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
async def hello_world():
    """
    Hello World 端點

    這是一個簡單的測試端點，用於驗證 API 是否正常運作。

    Returns:
        dict: 包含歡迎訊息的 JSON 回應
    """
    return {"message": "Hello, World!", "status": "success", "version": "v1"}
