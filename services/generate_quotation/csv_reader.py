#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 讀取模組
功能：讀取 CSV 檔案並轉換為 JSON 格式
"""

import csv
from typing import Any, Dict, List


class CSVReader:
    """CSV 讀取器"""

    def __init__(self):
        pass

    def read_csv_to_json(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """
        讀取 CSV 檔案並轉換為 JSON 格式

        Args:
            csv_file_path: CSV 檔案路徑

        Returns:
            包含所有客戶資料的 JSON 列表
        """
        invoices = []

        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                # 基本客戶資訊
                invoice_data = {
                    "customer_name": row.get("客戶名稱", ""),
                    "contact_person": row.get("聯絡人", ""),
                    "phone": row.get("電話", ""),
                    "tax_id": row.get("客戶統編", ""),
                    "invoice_number": row.get("發票號碼", ""),
                    "invoice_date": row.get("發票日期", ""),
                    "invoice_type": row.get("發票", ""),
                    "notes": row.get("備註", ""),
                    "items": [],
                }

                # 處理品項資料（最多4個品項）
                for i in range(1, 5):
                    item_name_key = f"品項{i}"
                    if i == 1:
                        quantity_key = "數量"
                        unit_price_key = "單價"
                    else:
                        quantity_key = f"數量{i}"
                        unit_price_key = f"單價{i}"

                    item_name = (row.get(item_name_key, "") or "").strip()
                    quantity = (row.get(quantity_key, "") or "").strip()
                    unit_price = (row.get(unit_price_key, "") or "").strip()

                    # 如果品項名稱不為空，則加入品項
                    if item_name:
                        invoice_data["items"].append(
                            {
                                "name": item_name,
                                "quantity": quantity,
                                "unit_price": unit_price,
                                "amount": "",  # 金額將由 PDF 生成器自動計算
                            }
                        )

                invoices.append(invoice_data)

        return invoices

    def validate_csv_format(self, csv_file_path: str) -> bool:
        """
        驗證 CSV 檔案格式是否正確

        Args:
            csv_file_path: CSV 檔案路徑

        Returns:
            格式是否正確
        """
        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames

                # 檢查必要的欄位
                required_fields = [
                    "客戶名稱",
                    "聯絡人",
                    "電話",
                    "客戶統編",
                    "發票號碼",
                    "發票日期",
                    "發票",
                    "備註",
                    "品項1",
                    "數量",
                    "單價",
                ]

                for field in required_fields:
                    if field not in headers:
                        print(f"✗ 缺少必要欄位: {field}")
                        return False

                print("✓ CSV 檔案格式驗證通過")
                return True

        except Exception as e:
            print(f"✗ CSV 檔案讀取錯誤: {e}")
            return False

    def get_csv_info(self, csv_file_path: str) -> Dict[str, Any]:
        """
        取得 CSV 檔案基本資訊

        Args:
            csv_file_path: CSV 檔案路徑

        Returns:
            CSV 檔案資訊
        """
        try:
            with open(csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames

                # 計算行數
                row_count = sum(1 for row in reader)

                return {
                    "file_path": csv_file_path,
                    "headers": headers,
                    "row_count": row_count,
                    "encoding": "utf-8",
                }
        except Exception as e:
            return {"error": str(e)}


def main():
    """測試 CSV 讀取功能"""
    reader = CSVReader()

    # 測試讀取 CSV
    csv_file = "invoice_data.csv"
    print(f"正在讀取 CSV 檔案: {csv_file}")

    # 驗證格式
    if not reader.validate_csv_format(csv_file):
        return

    # 取得檔案資訊
    info = reader.get_csv_info(csv_file)
    print(f"檔案資訊: {info}")

    # 讀取資料
    invoices = reader.read_csv_to_json(csv_file)
    print(f"✓ 成功讀取 {len(invoices)} 筆請款單資料")

    # 顯示第一筆資料
    if invoices:
        print("\n第一筆資料:")
        import json

        print(json.dumps(invoices[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
