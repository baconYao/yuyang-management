"""
Generate 請款單 PDF from invoice dict (same shape as services/generate_quotation).
Uses Jinja2 + WeasyPrint; writes to BytesIO and returns bytes.
"""

import io
import os
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration


def _format_currency(value: Any) -> str:
    try:
        if isinstance(value, str):
            value = float(value)
        return f"{value:,.0f}"
    except (ValueError, TypeError):
        return str(value)


def _calculate_totals(
    items: list[dict[str, Any]], invoice_type: str = ""
) -> dict[str, float]:
    subtotal = 0.0
    for item in items:
        try:
            amount = float(item.get("amount", 0)) if item.get("amount") else 0
            subtotal += amount
        except (ValueError, TypeError):
            continue
    if invoice_type == "三聯":
        tax_rate = 0.05
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
    else:
        tax_amount = 0.0
        total = subtotal
    return {"subtotal": subtotal, "tax": tax_amount, "total": total}


def _calculate_item_amount(quantity: str | float, unit_price: str | float) -> float:  # noqa: E501
    try:
        qty_str = str(quantity).strip()
        digits = "".join(filter(lambda x: x.isdigit() or x == ".", qty_str))
        qty_num = float(digits or "0")
        price_str = str(unit_price).strip()
        price_num = float(price_str)
        return qty_num * price_num
    except (ValueError, TypeError):
        return 0.0


def _prepare_invoice_data(invoice_data: dict[str, Any]) -> dict[str, Any]:
    """Prepare invoice data for template: item_list with display_quantity, totals."""  # noqa: E501
    processed_items: list[dict[str, Any]] = []
    for item in invoice_data.get("items", []):
        processed = dict(item)
        if not processed.get("amount") or processed.get("amount") == "":
            calculated = _calculate_item_amount(
                processed.get("quantity", ""),
                processed.get("unit_price", ""),
            )
            processed["amount"] = str(int(calculated)) if calculated > 0 else ""  # noqa: E501
        qty_raw = processed.get("quantity", "")
        qty_display = str(qty_raw)
        m = re.fullmatch(r"\s*(\d+)\s*月\s*", qty_display)
        if m:
            qty_display = f"{int(m.group(1))}個月"
        else:
            # Force quantity to int for PDF display (no decimals).
            try:
                qty_display = str(int(float(str(qty_raw).strip())))
            except (ValueError, TypeError):
                qty_display = str(qty_raw)
        processed["display_quantity"] = qty_display
        # Format numbers as display strings for PDF (avoid rendering issues)
        try:
            up = processed.get("unit_price")
            processed["display_unit_price"] = (
                _format_currency(up) if up is not None and up != "" else ""
            )
        except (ValueError, TypeError):
            processed["display_unit_price"] = str(processed.get("unit_price", ""))  # noqa: E501
        try:
            amt = processed.get("amount")
            processed["display_amount"] = (
                _format_currency(amt) if amt is not None and amt != "" else ""
            )
        except (ValueError, TypeError):
            processed["display_amount"] = str(processed.get("amount", ""))
        processed_items.append(processed)

    invoice_type = invoice_data.get("invoice_type", "")
    totals = _calculate_totals(processed_items, invoice_type)

    # invoice_issue_date = invoice_data.get("invoice_issue_date", "")
    # invoice_date = datetime.now().strftime("%Y-%m-%d")

    return {
        "bill_number": invoice_data.get("bill_number", ""),
        "customer_name": invoice_data.get("customer_name", ""),
        "contact_person": invoice_data.get("contact_person", ""),
        "phone": invoice_data.get("phone", ""),
        "invoice_title": invoice_data.get("invoice_title", ""),
        "invoice_number": invoice_data.get("invoice_number", ""),
        "invoice_date": "",
        "invoice_issue_date": "",
        "tax_id": invoice_data.get("tax_id", ""),
        "invoice_type": invoice_type,
        "notes": invoice_data.get("notes", ""),
        "address": invoice_data.get("address", ""),
        "item_list": processed_items,
        "totals": {
            "subtotal": _format_currency(totals["subtotal"]),
            "tax": _format_currency(totals["tax"]),
            "total": _format_currency(totals["total"]),
        },
    }


def generate_pdf_bytes(invoice_data: dict[str, Any]) -> bytes:
    """
    Generate PDF bytes for one invoice (請款單).

    Args:
        invoice_data: Dict with customer_name, invoice_title, contact_person,
        phone, tax_id, invoice_type ("三聯"/"二聯"/"無發票"), notes, items
        (each: name, quantity, unit_price, amount), optional
        invoice_number, invoice_issue_date.

    Returns:
        PDF file as bytes.
    """
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    font_config = FontConfiguration()
    prepared = _prepare_invoice_data(invoice_data)
    template = jinja_env.get_template("invoice.html")
    html_content = template.render(invoice=prepared)
    html_doc = HTML(string=html_content)
    css_path = os.path.join(template_dir, "styles.css")
    buffer = io.BytesIO()
    if os.path.exists(css_path):
        css_doc = CSS(filename=css_path, font_config=font_config)
        html_doc.write_pdf(
            buffer,
            stylesheets=[css_doc],
            font_config=font_config,
            optimize_images=True,
        )
    else:
        html_doc.write_pdf(
            buffer,
            font_config=font_config,
            optimize_images=True,
        )
    buffer.seek(0)
    return buffer.getvalue()
