"""Reusable PDF export for the admin (reportlab — pure Python, PA-friendly).

Used by admin actions to render the selected rows as a branded PDF table.
"""
from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BRAND = colors.HexColor("#a4182b")
STRIPE = colors.HexColor("#f7f7f8")
LINE = colors.HexColor("#e4e7ec")


def export_pdf_response(title, columns, rows, filename, subtitle=""):
    """Build a landscape A4 PDF table and return it as a download response."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        topMargin=16 * mm, bottomMargin=14 * mm, leftMargin=12 * mm, rightMargin=12 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("tb_title", parent=styles["Title"], textColor=BRAND, fontSize=18, spaceAfter=2)
    cell_style = ParagraphStyle("tb_cell", parent=styles["BodyText"], fontSize=8, leading=10)

    elements = [Paragraph(title, title_style)]
    if subtitle:
        elements.append(Paragraph(subtitle, ParagraphStyle("tb_sub", parent=styles["Normal"], textColor=colors.HexColor("#6b7280"), fontSize=9)))
    elements.append(Spacer(1, 8))

    # Wrap cells in Paragraphs so long text wraps instead of overflowing.
    body = [[Paragraph(str(c), cell_style) for c in row] for row in rows]
    data = [columns] + (body or [["—"] * len(columns)])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    doc.build(elements)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
