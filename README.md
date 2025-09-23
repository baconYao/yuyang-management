# CSV 轉 PDF 請款單生成器

這是一個模組化的 Python 程式，用於讀取 CSV 資料並產生 PDF 請款單。

## 功能特色

- **模組化設計**：分離 CSV 讀取和 PDF 生成邏輯
- **多種使用方式**：支援批量處理和單一請款單生成
- **格式驗證**：自動驗證 CSV 檔案格式
- **多品項支援**：支援最多 4 個品項的請款單
- **自動計算**：自動計算營業稅（5%）和總金額
- **中文字體支援**：優化繁體中文顯示

## 檔案結構

```
├── README.md             # 專案說明文件
├── LICENSE               # 授權檔案
└── service/
    └── generate_invoice/ # 請款單生成服務
        ├── main.py              # 主程式（整合功能）
        ├── csv_reader.py         # CSV 讀取模組
        ├── pdf_generator.py      # PDF 生成模組
        ├── invoice_data.csv      # 測試資料檔案
        └── requirements.txt      # 依賴套件清單
```

## 安裝需求

```bash
cd service/generate_invoice
pip install -r requirements.txt
```

## 使用方法

### 1. 進入服務目錄

```bash
cd service/generate_invoice
```

### 2. 主程式（推薦）

```bash
# 處理所有請款單
python3 main.py

# 列出所有請款單
python3 main.py list

# 生成單一請款單（編號從1開始）
python3 main.py single 1

# 顯示使用說明
python3 main.py help
```

### 3. 個別模組測試

```bash
# 測試 CSV 讀取功能
python3 csv_reader.py

# 測試 PDF 生成功能
python3 pdf_generator.py
```

## CSV 檔案格式說明

- **客戶名稱**: 客戶公司名稱
- **聯絡人**: 聯絡人姓名和職稱
- **電話**: 聯絡電話
- **發票號碼**: 發票編號
- **客戶統編**: 統一編號
- **發票**: 發票類型（二聯、三聯、無發票等）
- **備註**: 備註資訊
- **品項 1-4**: 最多支援 4 個品項
- **數量**: 品項數量
- **單價**: 品項單價
- **金額**: 品項金額

## 輸出格式

每筆資料會產生一頁請款單，包含：

- 公司標題（宇陽科技有限公司）
- 聯絡資訊
- 客戶基本資料
- 品項清單
- 金額計算（含營業稅 5%）

## 注意事項

- CSV 檔案必須使用 UTF-8 編碼
- 品項欄位如果為空，則不會顯示在請款單中
- 程式會自動計算總金額和營業稅
