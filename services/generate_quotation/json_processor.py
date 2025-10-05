#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 資料處理器
處理 JSON 格式的請款單資料
"""

import json
import os
from typing import Any, Dict, List, Union

from csv_reader import CSVReader


class JSONProcessor:
    """JSON 資料處理器"""

    def __init__(self):
        self.csv_reader = CSVReader()

    def csv_to_json_file(self, csv_file_path: str, json_file_path: str):
        """
        將 CSV 檔案轉換為 JSON 檔案

        Args:
            csv_file_path: CSV 檔案路徑
            json_file_path: 輸出 JSON 檔案路徑
        """
        try:
            # 讀取 CSV 資料
            invoices = self.csv_reader.read_csv_to_json(csv_file_path)

            # 寫入 JSON 檔案
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(invoices, f, ensure_ascii=False, indent=2)

            print(f"✓ CSV 已轉換為 JSON：{json_file_path}")
            print(f"  包含 {len(invoices)} 筆請款單資料")

        except Exception as e:
            print(f"✗ CSV 轉 JSON 失敗：{e}")
            raise

    def load_json_file(
        self, json_file_path: str
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        載入 JSON 檔案

        Args:
            json_file_path: JSON 檔案路徑

        Returns:
            JSON 資料
        """
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"✓ JSON 檔案已載入：{json_file_path}")
            return data

        except Exception as e:
            print(f"✗ JSON 檔案載入失敗：{e}")
            raise

    def save_json_file(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]], json_file_path: str
    ):
        """
        儲存資料為 JSON 檔案

        Args:
            data: 要儲存的資料
            json_file_path: JSON 檔案路徑
        """
        try:
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✓ 資料已儲存為 JSON：{json_file_path}")

        except Exception as e:
            print(f"✗ JSON 檔案儲存失敗：{e}")
            raise

    def validate_json_structure(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """
        驗證 JSON 資料結構

        Args:
            data: JSON 資料

        Returns:
            結構是否正確
        """
        try:
            if isinstance(data, list):
                # 多個請款單
                for invoice in data:
                    if not self._validate_single_invoice(invoice):
                        return False
            else:
                # 單一請款單
                if not self._validate_single_invoice(data):
                    return False

            print("✓ JSON 資料結構驗證通過")
            return True

        except Exception as e:
            print(f"✗ JSON 資料結構驗證失敗：{e}")
            return False

    def _validate_single_invoice(self, invoice: Dict[str, Any]) -> bool:
        """
        驗證單一請款單結構

        Args:
            invoice: 請款單資料

        Returns:
            結構是否正確
        """
        required_fields = [
            "customer_name",
            "contact_person",
            "phone",
            "tax_id",
            "invoice_number",
            "invoice_date",
            "invoice_type",
            "notes",
            "items",
        ]
        
        # 可選欄位（發票日期）
        optional_fields = [
            "invoice_issue_date",
        ]

        for field in required_fields:
            if field not in invoice:
                print(f"✗ 缺少必要欄位：{field}")
                return False

        # 驗證品項結構
        if not isinstance(invoice["items"], list):
            print("✗ items 必須是列表")
            return False

        for item in invoice["items"]:
            item_fields = ["name", "quantity", "unit_price", "amount"]
            for field in item_fields:
                if field not in item:
                    print(f"✗ 品項缺少必要欄位：{field}")
                    return False

        return True

    def get_json_info(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        取得 JSON 資料資訊

        Args:
            data: JSON 資料

        Returns:
            資料資訊
        """
        if isinstance(data, list):
            # 多個請款單
            total_items = sum(len(invoice.get("items", [])) for invoice in data)
            total_amount = 0

            for invoice in data:
                for item in invoice.get("items", []):
                    try:
                        amount = (
                            float(item.get("amount", 0)) if item.get("amount") else 0
                        )
                        total_amount += amount
                    except (ValueError, TypeError):
                        continue

            return {
                "type": "multiple_invoices",
                "invoice_count": len(data),
                "total_items": total_items,
                "total_amount": total_amount,
                "tax_amount": total_amount * 0.05,
                "final_total": total_amount * 1.05,
            }
        else:
            # 單一請款單
            items = data.get("items", [])
            total_amount = 0

            for item in items:
                try:
                    amount = float(item.get("amount", 0)) if item.get("amount") else 0
                    total_amount += amount
                except (ValueError, TypeError):
                    continue

            return {
                "type": "single_invoice",
                "customer_name": data.get("customer_name", ""),
                "item_count": len(items),
                "total_amount": total_amount,
                "tax_amount": total_amount * 0.05,
                "final_total": total_amount * 1.05,
            }

    def create_sample_json(self, output_path: str):
        """
        建立範例 JSON 檔案

        Args:
            output_path: 輸出檔案路徑
        """
        sample_data = [
            {
                "customer_name": "範例公司A",
                "contact_person": "張三",
                "phone": "03-1234567",
                "tax_id": "12345678",
                "invoice_number": "INV-001",
                "invoice_date": "2024-01-15",
                "invoice_issue_date": "2024-01-14",
                "invoice_type": "二聯",
                "notes": "範例備註",
                "items": [
                    {
                        "name": "範例品項1",
                        "quantity": "1",
                        "unit_price": "1000",
                        "amount": "1000",
                    },
                    {
                        "name": "範例品項2",
                        "quantity": "2",
                        "unit_price": "500",
                        "amount": "1000",
                    },
                ],
            },
            {
                "customer_name": "範例公司B",
                "contact_person": "李四",
                "phone": "03-7654321",
                "tax_id": "87654321",
                "invoice_number": "INV-002",
                "invoice_date": "2024-01-16",
                "invoice_issue_date": "2024-01-15",
                "invoice_type": "三聯",
                "notes": "另一個範例",
                "items": [
                    {
                        "name": "範例品項3",
                        "quantity": "3",
                        "unit_price": "300",
                        "amount": "900",
                    }
                ],
            },
        ]

        self.save_json_file(sample_data, output_path)
        print(f"✓ 範例 JSON 檔案已建立：{output_path}")

    def convert_csv_to_json(self, csv_file_path: str, json_file_path: str = None):
        """
        將 CSV 檔案轉換為 JSON 檔案（便利方法）

        Args:
            csv_file_path: CSV 檔案路徑
            json_file_path: 輸出 JSON 檔案路徑（可選）
        """
        if json_file_path is None:
            base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
            json_file_path = f"{base_name}.json"

        self.csv_to_json_file(csv_file_path, json_file_path)

        # 驗證轉換結果
        data = self.load_json_file(json_file_path)
        self.validate_json_structure(data)

        # 顯示資訊
        info = self.get_json_info(data)
        print(f"轉換資訊：{info}")


def main():
    """測試 JSON 處理功能"""
    processor = JSONProcessor()

    # 測試 CSV 轉 JSON
    csv_file = "invoice_data.csv"
    json_file = "invoice_data.json"

    if os.path.exists(csv_file):
        print("正在轉換 CSV 為 JSON...")
        processor.convert_csv_to_json(csv_file, json_file)

        # 測試載入和驗證
        print("\n正在驗證 JSON 資料...")
        data = processor.load_json_file(json_file)
        processor.validate_json_structure(data)

        # 顯示資訊
        info = processor.get_json_info(data)
        print(f"\nJSON 資料資訊：{info}")
    else:
        print("CSV 檔案不存在，建立範例 JSON...")
        processor.create_sample_json("sample_invoices.json")


if __name__ == "__main__":
    main()
