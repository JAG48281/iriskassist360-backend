
# app/utils/pdf_generator.py
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from typing import Dict

def generate_premium_pdf(quote: Dict) -> bytes:
    """
    Simple PDF generator that creates a one-page summary.
    Returns raw PDF bytes.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 60
    line_height = 16

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "iRiskAssist360 - Premium Summary")
    y -= (line_height * 2)

    c.setFont("Helvetica", 11)
    # Render key: value pairs from the quote dict
    for key, value in quote.items():
        # Convert nested dicts to string
        if isinstance(value, dict):
            text = f"{key}:"
            c.drawString(x, y, text)
            y -= line_height
            for k2, v2 in value.items():
                c.drawString(x + 20, y, f"{k2}: {v2}")
                y -= line_height
        else:
            c.drawString(x, y, f"{key}: {value}")
            y -= line_height

        # Add new page if space is low (very simple)
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
