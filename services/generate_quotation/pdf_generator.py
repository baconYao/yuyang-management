#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML PDF 生成器
使用 Jinja2 + WeasyPrint 生成 PDF 請款單
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration
import re


class HTMLPDFGenerator:
    """HTML PDF 生成器"""

    def __init__(self, template_dir: str = "templates"):
        """
        初始化 HTML PDF 生成器

        Args:
            template_dir: 模板目錄路徑
        """
        self.template_dir = template_dir
        self.setup_jinja()
        self.setup_fonts()

    def setup_jinja(self):
        """設定 Jinja2 環境"""
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 添加自定義過濾器
        self.jinja_env.filters["currency"] = self.format_currency
        self.jinja_env.filters["number"] = self.format_number

    def setup_fonts(self):
        """設定字體配置"""
        self.font_config = FontConfiguration()

    def format_currency(self, value: Any) -> str:
        """格式化貨幣"""
        try:
            if isinstance(value, str):
                value = float(value)
            return f"{value:,.0f}"
        except (ValueError, TypeError):
            return str(value)

    def format_number(self, value: Any) -> str:
        """格式化數字"""
        try:
            if isinstance(value, str):
                value = float(value)
            return f"{value:,.0f}"
        except (ValueError, TypeError):
            return str(value)

    def get_current_date(self) -> str:
        """取得當前日期（yyyy-mm-dd 格式）"""
        return datetime.now().strftime("%Y-%m-%d")

    def calculate_totals(self, items: List[Dict[str, Any]], invoice_type: str = "") -> Dict[str, float]:
        """
        計算總金額

        Args:
            items: 品項列表
            invoice_type: 發票種類

        Returns:
            包含小計、稅額、總計的字典
        """
        subtotal = 0

        for item in items:
            try:
                amount = float(item.get("amount", 0)) if item.get("amount") else 0
                subtotal += amount
            except (ValueError, TypeError):
                continue

        # 根據發票種類決定是否計算稅金
        # 只有「三聯」需計算 5% 營業稅；二聯與無發票不計稅
        if invoice_type == "三聯":
            tax_rate = 0.05  # 營業稅 5%
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount
        else:
            tax_amount = 0
            total = subtotal

        return {"subtotal": subtotal, "tax": tax_amount, "total": total}

    def calculate_item_amount(self, quantity: str, unit_price: str) -> float:
        """
        計算品項金額（數量 × 單價）

        Args:
            quantity: 數量
            unit_price: 單價

        Returns:
            計算後的金額
        """
        try:
            # 處理數量（可能包含單位，如 "2 包"）
            qty_str = str(quantity).strip()
            # 提取數字部分
            qty_num = float(''.join(filter(lambda x: x.isdigit() or x == '.', qty_str)))
            
            # 處理單價
            price_str = str(unit_price).strip()
            price_num = float(price_str)
            
            return qty_num * price_num
        except (ValueError, TypeError):
            return 0.0

    def prepare_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        準備請款單資料

        Args:
            invoice_data: 原始請款單資料

        Returns:
            處理後的請款單資料
        """
        # 處理品項資料，自動計算金額
        processed_items = []
        for item in invoice_data.get("items", []):
            processed_item = item.copy()
            
            # 如果金額為空，自動計算
            if not processed_item.get("amount") or processed_item.get("amount") == "":
                calculated_amount = self.calculate_item_amount(
                    processed_item.get("quantity", ""),
                    processed_item.get("unit_price", "")
                )
                processed_item["amount"] = str(int(calculated_amount)) if calculated_amount > 0 else ""
            
            # 顯示用數量：將「數字月」改為「數字個月」
            qty_display = str(processed_item.get("quantity", ""))
            m = re.fullmatch(r"\s*(\d+)\s*月\s*", qty_display)
            if m:
                qty_display = f"{m.group(1)}個月"
            processed_item["display_quantity"] = qty_display
            
            processed_items.append(processed_item)

        # 計算總金額（傳遞發票種類）
        invoice_type = invoice_data.get("invoice_type", "")
        totals = self.calculate_totals(processed_items, invoice_type)

        # 處理日期欄位
        invoice_date = self.get_current_date()  # 請款日期（系統生成）
        invoice_issue_date = invoice_data.get("invoice_issue_date", "")  # 發票日期（從資料取得）

        # 準備完整的請款單資料
        prepared_data = {
            "customer_name": invoice_data.get("customer_name", ""),
            "contact_person": invoice_data.get("contact_person", ""),
            "phone": invoice_data.get("phone", ""),
            "invoice_title": invoice_data.get("invoice_title", ""),
            "invoice_number": invoice_data.get("invoice_number", ""),
            "invoice_date": invoice_date,  # 請款日期（系統生成）
            "invoice_issue_date": invoice_issue_date,  # 發票日期
            "tax_id": invoice_data.get("tax_id", ""),
            "invoice_type": invoice_data.get("invoice_type", ""),
            "notes": invoice_data.get("notes", ""),
            "item_list": processed_items,  # 使用處理後的品項資料
            "totals": {
                "subtotal": self.format_currency(totals["subtotal"]),
                "tax": self.format_currency(totals["tax"]),
                "total": self.format_currency(totals["total"]),
            },
            # 稅額說明：二聯顯示「已包含」
            "tax_note": "已包含" if invoice_type == "二聯" else "",
        }

        return prepared_data

    def generate_html(
        self, invoice_data: Dict[str, Any], template_name: str = "invoice.html"
    ) -> str:
        """
        生成 HTML 內容

        Args:
            invoice_data: 請款單資料
            template_name: 模板檔案名稱

        Returns:
            生成的 HTML 字串
        """
        template = self.jinja_env.get_template(template_name)
        prepared_data = self.prepare_invoice_data(invoice_data)
        html_content = template.render(invoice=prepared_data)
        return html_content

    def generate_pdf(
        self,
        invoice_data: Dict[str, Any],
        output_path: str,
        template_name: str = "invoice.html",
    ):
        """
        生成 PDF 檔案

        Args:
            invoice_data: 請款單資料
            output_path: 輸出 PDF 檔案路徑
            template_name: 模板檔案名稱
        """
        try:
            # 生成 HTML 內容
            html_content = self.generate_html(invoice_data, template_name)

            # 建立 HTML 物件
            html_doc = HTML(string=html_content)

            # CSS 檔案路徑
            css_path = os.path.join(self.template_dir, "styles.css")

            # 生成 PDF
            if os.path.exists(css_path):
                css_doc = CSS(filename=css_path, font_config=self.font_config)
                html_doc.write_pdf(
                    output_path, 
                    stylesheets=[css_doc], 
                    font_config=self.font_config,
                    optimize_images=True
                )
            else:
                html_doc.write_pdf(
                    output_path, 
                    font_config=self.font_config,
                    optimize_images=True
                )

            print(f"✓ PDF 已生成：{output_path}")

        except Exception as e:
            print(f"✗ PDF 生成失敗：{e}")
            raise

    def generate_multiple_pdfs(
        self,
        invoices: List[Dict[str, Any]],
        output_path: str,
        template_name: str = "invoice.html",
    ):
        """
        生成多個請款單的 PDF（合併到一個檔案）

        Args:
            invoices: 請款單資料列表
            output_path: 輸出 PDF 檔案路徑
            template_name: 模板檔案名稱
        """
        try:
            # 為每個請款單生成 HTML
            html_contents = []
            for i, invoice_data in enumerate(invoices):
                html_content = self.generate_html(invoice_data, template_name)

                # 如果不是最後一個，添加分頁符
                if i < len(invoices) - 1:
                    html_content += '<div class="page-break"></div>'

                html_contents.append(html_content)

            # 合併所有 HTML 內容
            combined_html = "\n".join(html_contents)

            # 建立 HTML 物件
            html_doc = HTML(string=combined_html)

            # CSS 檔案路徑
            css_path = os.path.join(self.template_dir, "styles.css")

            # 生成 PDF
            if os.path.exists(css_path):
                css_doc = CSS(filename=css_path, font_config=self.font_config)
                html_doc.write_pdf(
                    output_path, stylesheets=[css_doc], font_config=self.font_config
                )
            else:
                html_doc.write_pdf(output_path, font_config=self.font_config)

            print(f"✓ 多頁 PDF 已生成：{output_path}")

        except Exception as e:
            print(f"✗ 多頁 PDF 生成失敗：{e}")
            raise

    def generate_from_json(
        self, json_file_path: str, output_path: str, template_name: str = "invoice.html"
    ):
        """
        從 JSON 檔案生成 PDF

        Args:
            json_file_path: JSON 檔案路徑
            output_path: 輸出 PDF 檔案路徑
            template_name: 模板檔案名稱
        """
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 判斷是單一請款單還是多個請款單
            if isinstance(data, list):
                self.generate_multiple_pdfs(data, output_path, template_name)
            else:
                self.generate_pdf(data, output_path, template_name)

        except Exception as e:
            print(f"✗ 從 JSON 生成 PDF 失敗：{e}")
            raise

    def get_invoice_info(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        取得請款單資訊

        Args:
            invoice_data: 請款單資料

        Returns:
            請款單資訊
        """
        invoice_type = invoice_data.get("invoice_type", "")
        totals = self.calculate_totals(invoice_data.get("items", []), invoice_type)

        return {
            "customer_name": invoice_data.get("customer_name", ""),
            "item_count": len(invoice_data.get("items", [])),
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "total": totals["total"],
        }


def main():
    """測試 HTML PDF 生成功能"""
    generator = HTMLPDFGenerator()

    # 測試資料
    test_invoice = {
        "customer_name": "測試公司",
        "contact_person": "測試聯絡人",
        "phone": "03-1234567",
        "invoice_number": "TEST-001",
        "invoice_issue_date": "2024-01-15",  # 發票日期
        "tax_id": "12345678",
        "invoice_type": "二聯",
        "notes": "測試備註",
        "items": [
            {
                "name": "測試品項1",
                "quantity": "1",
                "unit_price": "100",
                "amount": "100",
            },
            {
                "name": "測試品項2",
                "quantity": "2",
                "unit_price": "200",
                "amount": "400",
            },
        ],
    }

    # 生成測試 PDF
    output_file = "test_html_invoice.pdf"
    print("正在生成 HTML PDF...")
    generator.generate_pdf(test_invoice, output_file)

    # 顯示請款單資訊
    info = generator.get_invoice_info(test_invoice)
    print(f"請款單資訊: {info}")


if __name__ == "__main__":
    main()
