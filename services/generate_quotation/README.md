# 請款單生成服務

這是宇陽科技有限公司的請款單生成服務，使用 Jinja2 + WeasyPrint 的現代化模板系統生成高品質 PDF 請款單。

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 使用服務

```bash
# 從 CSV 生成 PDF
python3 main.py csv

# 從 JSON 生成 PDF
python3 main.py json invoice_data.json

# 將 CSV 轉換為 JSON
python3 main.py convert

# 建立範例資料
python3 main.py sample

# 顯示說明
python3 main.py help
```

## 檔案說明

- `main.py` - 主程式
- `pdf_generator.py` - PDF 生成器
- `csv_reader.py` - CSV 讀取模組
- `json_processor.py` - JSON 資料處理器
- `templates/invoice.html` - HTML 模板
- `templates/styles.css` - CSS 樣式
- `invoice_data.csv` - 測試資料檔案
- `invoice_data.json` - JSON 格式資料
- `requirements.txt` - 依賴套件清單

## 功能特色

- ✅ **現代化模板**：使用 Jinja2 + WeasyPrint
- ✅ **CSS 樣式**：支援複雜的視覺設計
- ✅ **中文字體**：優化的繁體中文顯示
- ✅ **JSON 支援**：可直接從 JSON 檔案生成
- ✅ **響應式設計**：適應不同頁面大小
- ✅ **高品質輸出**：專業的 PDF 格式
- ✅ **格式驗證**：自動檢查資料格式
- ✅ **批量處理**：支援多筆請款單

## 輸出格式

每筆資料會產生一頁請款單，包含：

- 公司標題：宇陽科技有限公司
- 聯絡資訊：TEL: 037-474982, FAX: 037-474989
- 客戶資料表格
- 品項清單表格
- 金額計算（含營業稅 5%）

## 注意事項

1. CSV 檔案必須使用 UTF-8 編碼
2. 品項欄位如果為空，則不會顯示在請款單中
3. 程式會自動計算總金額和營業稅（5%）
4. 每筆資料會產生獨立的請款單頁面
5. 所有請款單會合併到同一個 PDF 檔案中
