from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.v1 import router as v1_router
from app.database.session import create_db_tables


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_tables()
    yield


app = FastAPI(
    title="Yuyang Management API",
    description="宇陽科技管理系統",
    version="1.0.0",
    docs_url=None,  # 禁用默認的 Swagger UI
    redoc_url=None,  # 禁用默認的 ReDoc
    lifespan=lifespan_handler,
)


# 整合 Scalar API 文檔
@app.get("/docs", include_in_schema=False)
async def scalar_html():
    """
    Scalar API 文檔頁面
    """
    openapi_url = app.openapi_url
    return HTMLResponse(
        content=f"""
<!doctype html>
<html>
  <head>
    <title>Scalar API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
  </head>
  <body>
    <script
      id="api-reference"
      data-spec-url="{openapi_url}"
      data-configuration='{{"theme": "purple", "layout": "modern"}}'
    ></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
        """,
        status_code=200,
    )


@app.get("/", include_in_schema=False)
async def root():
    """
    根路徑 - API 歡迎訊息
    """
    return {
        "message": "Welcome to Yuyang Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_versions": ["v1"],
    }


# 註冊 API 版本路由
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
