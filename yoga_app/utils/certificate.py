"""
Certificate generation utility for Yoga Kailasa.
Produces a branded A4-landscape PDF using ReportLab.
"""
from __future__ import annotations

import datetime
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


def _hex_to_rgb(hex_colour: str) -> tuple[float, float, float]:
    """Convert a hex colour string like '#855300' to an (r, g, b) tuple in 0-1 range."""
    hex_colour = hex_colour.lstrip("#")
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return r, g, b


def generate_certificate(user, course, completion_date: datetime.date | None = None) -> bytes | None:
    """
    Generate a branded PDF certificate using ReportLab.

    Returns raw PDF bytes on success, None on failure (logs error).
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.fonts import addMapping

        # --- Data preparation ---
        display_name: str = user.get_full_name() or user.username
        cert_id: str = f"YK-{user.id}-{course.id}"
        date_obj = completion_date or datetime.date.today()
        # Format: "Month DD, YYYY"  e.g. "January 05, 2025"
        completion_date_str: str = date_obj.strftime("%B %d, %Y")
        course_title: str = str(course.title)

        # --- Colours ---
        BRAND       = _hex_to_rgb("#855300")   # header / display name
        SUBTITLE_C  = _hex_to_rgb("#534434")   # subtitle
        BODY_DARK   = _hex_to_rgb("#1f1b14")   # course title
        BODY_MID    = _hex_to_rgb("#867461")   # completion date
        FOOTER_C    = _hex_to_rgb("#b0a090")   # certificate ID

        # --- Page setup ---
        page_w, page_h = landscape(A4)   # 841 × 595 pt
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_w, page_h))

        # --- Background (white) ---
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        # --- Decorative border ---
        inset = 20
        c.setStrokeColorRGB(*BRAND)
        c.setLineWidth(3)
        c.rect(inset, inset, page_w - 2 * inset, page_h - 2 * inset, fill=0, stroke=1)
        # Inner thin border for decoration
        c.setLineWidth(1)
        c.rect(inset + 6, inset + 6, page_w - 2 * (inset + 6), page_h - 2 * (inset + 6), fill=0, stroke=1)

        # --- Helper: centred text ---
        def draw_centred(text: str, y: float, font: str, size: float, colour: tuple) -> None:
            c.setFont(font, size)
            c.setFillColorRGB(*colour)
            c.drawCentredString(page_w / 2, y, text)

        # --- Header: "Yoga Kailasa" ---
        draw_centred("Yoga Kailasa", page_h - 80, "Times-Bold", 36, BRAND)

        # --- Subtitle: "Certificate of Completion" ---
        draw_centred("Certificate of Completion", page_h - 120, "Times-Roman", 24, SUBTITLE_C)

        # --- Horizontal rule below subtitle ---
        rule_y = page_h - 135
        c.setStrokeColorRGB(*BRAND)
        c.setLineWidth(1)
        c.line(page_w * 0.2, rule_y, page_w * 0.8, rule_y)

        # --- Body ---
        draw_centred("This certifies that", page_h - 185, "Helvetica", 14, (0.3, 0.3, 0.3))
        draw_centred(display_name, page_h - 225, "Times-Bold", 28, BRAND)
        draw_centred("has successfully completed", page_h - 265, "Helvetica", 14, (0.3, 0.3, 0.3))
        draw_centred(course_title, page_h - 305, "Times-Bold", 22, BODY_DARK)
        draw_centred(completion_date_str, page_h - 345, "Helvetica", 12, BODY_MID)

        # --- Footer: Certificate ID ---
        footer_text = f"Certificate ID: {cert_id}"
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(*FOOTER_C)
        c.drawCentredString(page_w / 2, inset + 14, footer_text)

        c.save()
        return buffer.getvalue()

    except Exception as exc:
        logger.error(
            "Certificate generation failed for user %s course %s: %s",
            getattr(user, "id", "?"),
            getattr(course, "id", "?"),
            exc,
        )
        return None
