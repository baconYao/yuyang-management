#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 請款單生成器主程式
使用 Jinja2 + WeasyPrint 生成 PDF 請款單
"""

import os
import sys

from csv_reader import CSVReader
from json_processor import JSONProcessor
from pdf_generator import HTMLPDFGenerator


class InvoiceProcessor:
    """請款單處理器"""

    def __init__(self):
        self.csv_reader = CSVReader()
        self.html_generator = HTMLPDFGenerator()
        self.json_processor = JSONProcessor()

    def process_csv_to_pdf(self, csv_file_path: str, output_path: str = None):
        """
        處理 CSV 檔案並生成 PDF 請款單

        Args:
            csv_file_path: CSV 檔案路徑
            output_path: 輸出 PDF 檔案路徑（可選）
        """
        try:
            # 檢查 CSV 檔案是否存在
            if not os.path.exists(csv_file_path):
                print(f"✗ 錯誤：找不到 CSV 檔案 {csv_file_path}")
                return False

            # 驗證 CSV 格式
            print("正在驗證 CSV 檔案格式...")
            if not self.csv_reader.validate_csv_format(csv_file_path):
                return False

            # 讀取 CSV 資料
            print("正在讀取 CSV 檔案...")
            invoices = self.csv_reader.read_csv_to_json(csv_file_path)
            print(f"✓ 成功讀取 {len(invoices)} 筆請款單資料")

            # 顯示處理資訊
            csv_info = self.csv_reader.get_csv_info(csv_file_path)
            json_info = self.json_processor.get_json_info(invoices)

            print("\n處理資訊:")
            print(f"  CSV 檔案: {csv_info.get('file_path', 'N/A')}")
            print(f"  資料筆數: {csv_info.get('row_count', 0)}")
            print(f"  品項總數: {json_info['total_items']}")
            print(f"  總金額: {json_info['total_amount']:.0f}")
            print(f"  營業稅: {json_info['tax_amount']:.0f}")
            print(f"  最終總計: {json_info['final_total']:.0f}")

            # 設定輸出檔案路徑
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
                output_path = f"{base_name}_html.pdf"

            # 生成 PDF
            print("\n正在生成 PDF 請款單...")
            self.html_generator.generate_multiple_pdfs(invoices, output_path)

            print(f"✓ 處理完成！PDF 檔案已生成：{output_path}")
            return True

        except Exception as e:
            print(f"✗ 處理過程中發生錯誤：{str(e)}")
            return False

    def process_json_to_pdf(self, json_file_path: str, output_path: str = None):
        """
        處理 JSON 檔案並生成 PDF 請款單

        Args:
            json_file_path: JSON 檔案路徑
            output_path: 輸出 PDF 檔案路徑（可選）
        """
        try:
            # 檢查 JSON 檔案是否存在
            if not os.path.exists(json_file_path):
                print(f"✗ 錯誤：找不到 JSON 檔案 {json_file_path}")
                return False

            # 載入 JSON 資料
            print("正在載入 JSON 檔案...")
            data = self.json_processor.load_json_file(json_file_path)

            # 驗證 JSON 結構
            print("正在驗證 JSON 資料結構...")
            if not self.json_processor.validate_json_structure(data):
                return False

            # 顯示資料資訊
            json_info = self.json_processor.get_json_info(data)
            print("\nJSON 資料資訊:")
            if json_info["type"] == "multiple_invoices":
                print(f"  請款單數量: {json_info['invoice_count']}")
                print(f"  品項總數: {json_info['total_items']}")
                print(f"  總金額: {json_info['total_amount']:.0f}")
                print(f"  營業稅: {json_info['tax_amount']:.0f}")
                print(f"  最終總計: {json_info['final_total']:.0f}")
            else:
                print(f"  客戶名稱: {json_info['customer_name']}")
                print(f"  品項數量: {json_info['item_count']}")
                print(f"  總金額: {json_info['total_amount']:.0f}")
                print(f"  營業稅: {json_info['tax_amount']:.0f}")
                print(f"  最終總計: {json_info['final_total']:.0f}")

            # 設定輸出檔案路徑
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(json_file_path))[0]
                output_path = f"{base_name}_html.pdf"

            # 生成 PDF
            print("\n正在生成 PDF 請款單...")
            self.html_generator.generate_from_json(json_file_path, output_path)

            print(f"✓ 處理完成！PDF 檔案已生成：{output_path}")
            return True

        except Exception as e:
            print(f"✗ 處理過程中發生錯誤：{str(e)}")
            return False

    def convert_csv_to_json(self, csv_file_path: str, json_file_path: str = None):
        """
        將 CSV 檔案轉換為 JSON 檔案

        Args:
            csv_file_path: CSV 檔案路徑
            json_file_path: 輸出 JSON 檔案路徑（可選）
        """
        try:
            if json_file_path is None:
                base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
                json_file_path = f"{base_name}.json"

            print("正在將 CSV 轉換為 JSON...")
            self.json_processor.convert_csv_to_json(csv_file_path, json_file_path)

            return True

        except Exception as e:
            print(f"✗ CSV 轉 JSON 失敗：{str(e)}")
            return False

    def create_sample_data(self):
        """建立範例資料"""
        try:
            print("正在建立範例 JSON 資料...")
            self.json_processor.create_sample_json("sample_invoices.json")

            print("正在建立範例 PDF...")
            sample_data = self.json_processor.load_json_file("sample_invoices.json")
            self.html_generator.generate_from_json(
                "sample_invoices.json", "sample_invoices.pdf"
            )

            print("✓ 範例資料已建立")
            return True

        except Exception as e:
            print(f"✗ 建立範例資料失敗：{str(e)}")
            return False


def main():
    """主程式入口"""
    processor = InvoiceProcessor()

    # 預設檔案
    csv_file = "invoice_data.csv"
    json_file = "invoice_data.json"

    # 檢查命令列參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "csv":
            # 從 CSV 生成 PDF
            processor.process_csv_to_pdf(csv_file)

        elif command == "json":
            # 從 JSON 生成 PDF
            if len(sys.argv) > 2:
                json_file = sys.argv[2]
            processor.process_json_to_pdf(json_file)

        elif command == "convert":
            # 將 CSV 轉換為 JSON
            processor.convert_csv_to_json(csv_file, json_file)

        elif command == "sample":
            # 建立範例資料
            processor.create_sample_data()

        elif command == "help":
            # 顯示說明
            print("=== PDF 請款單生成器使用說明 ===")
            print("python3 main.py csv              # 從 CSV 生成 PDF")
            print("python3 main.py json [檔案]      # 從 JSON 生成 PDF")
            print("python3 main.py convert          # 將 CSV 轉換為 JSON")
            print("python3 main.py sample           # 建立範例資料")
            print("python3 main.py help             # 顯示此說明")
            print("\n特色功能:")
            print("- 使用 Jinja2 + WeasyPrint 生成高品質 PDF")
            print("- 支援 HTML/CSS 模板，可自訂樣式")
            print("- 支援中文字體和複雜排版")
            print("- 可從 CSV 或 JSON 檔案生成 PDF")

        else:
            print("✗ 未知的命令，請使用 'python3 main.py help' 查看說明")

    else:
        # 預設：從 CSV 生成 PDF
        processor.process_csv_to_pdf(csv_file)


if __name__ == "__main__":
    main()
