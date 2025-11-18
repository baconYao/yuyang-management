# Yuyang Management API

FastAPI 後端 RESTful API 服務，整合 Scalar API 文檔。

## 功能特色

- ✅ FastAPI 框架
- ✅ Scalar API 文檔整合
- ✅ API 版本化支援（v1）
- ✅ Docker 容器化支援
- ✅ 使用 uv 管理套件
- ✅ Pytest 測試框架

## 專案結構

```
backend/
├── app/                      # 應用程式碼
│   ├── __init__.py
│   ├── main.py              # FastAPI 應用主文件
│   └── api/
│       └── v1/              # API v1 版本
│           ├── __init__.py
│           └── customers.py      # Customers 端點
├── tests/                    # 測試檔案
│   ├── __init__.py
│   ├── conftest.py          # Pytest 配置和共用 fixtures
│   ├── test_main.py         # 主應用測試
│   └── test_api_v1.py       # API v1 測試
├── pyproject.toml           # uv 依賴管理
├── pytest.ini              # Pytest 配置
├── Dockerfile               # Docker 構建文件
├── docker-compose.yml       # Docker Compose 配置
├── .dockerignore           # Docker 忽略文件
└── README.md               # 本文件
```

## 快速開始

### 本地開發

1. 安裝 uv（如果尚未安裝）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 進入專案目錄並安裝依賴：

```bash
cd backend
uv pip install -e .
uv pip install -e ".[dev]"  # 安裝開發依賴（包含 pytest）
```

3. 啟動服務：

```bash
uvicorn app.main:app --reload
```

或使用 Python：

```bash
python -m app.main
```

4. 訪問 API：

- API 文檔：http://localhost:8000/docs
- API 根路徑：http://localhost:8000/

### Docker 部署

1. 進入專案目錄：

```bash
cd backend
```

2. 構建映像：

```bash
docker build -t yuyang-api .
```

3. 運行容器：

```bash
docker run -p 8000:8000 yuyang-api
```

或使用 Docker Compose：

```bash
docker-compose up
```

4. 訪問 API：

- API 文檔：http://localhost:8000/docs
- API 根路徑：http://localhost:8000/

## API 版本化

API 採用版本化設計，目前支援：

- **v1**: 第一個 API 版本

所有 v1 版本的端點都位於 `/api/v1/` 路徑下。

未來如需新增 API 版本，可以在 `app/api/` 目錄下建立新的版本目錄（如 `v2/`），並在主應用中註冊新的路由。

## 測試

### 執行測試

1. 確保已安裝開發依賴：

```bash
uv pip install -e ".[dev]"
```

2. 執行所有測試：

```bash
pytest
```

3. 執行測試並顯示詳細輸出：

```bash
pytest -v
```

4. 執行特定測試檔案：

```bash
pytest tests/test_main.py
pytest tests/test_api_v1.py
```

5. 執行測試並顯示覆蓋率（需要安裝 pytest-cov）：

```bash
pytest --cov=app --cov-report=html
```

## 開發說明

### 專案結構說明

- `app/main.py`: FastAPI 應用程式的主入口點，包含應用程式初始化、Scalar 文檔整合和路由註冊
- `app/api/v1/`: v1 版本的 API 端點目錄
- `pyproject.toml`: 使用 uv 管理的專案依賴配置
- `Dockerfile`: Docker 容器化構建配置，使用 uv 進行依賴管理

### 新增 API 端點

1. 在 `app/api/v1/` 目錄下建立新的端點檔案（如 `users.py`）
2. 在檔案中定義 `APIRouter` 和端點
3. 在 `app/api/v1/__init__.py` 中註冊新的路由
