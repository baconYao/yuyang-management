"""PDF generation for bills (請款單) using Jinja2 + WeasyPrint."""

from app.pdf.generator import generate_pdf_bytes

__all__ = ["generate_pdf_bytes"]
