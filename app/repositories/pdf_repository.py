import os

from fpdf import FPDF

FLAG_COLORS = {
    "zh": {"field": (222, 41, 16), "accent": (255, 222, 0)},
    "ja": {"field": (255, 255, 255), "accent": (188, 0, 45)},
    "vi": {"field": (218, 37, 29), "accent": (255, 205, 0)},
}

COUNTRY_NAMES = {"zh": "China", "ja": "Japan", "vi": "Vietnam"}

# macOS system font covering Latin, CJK, and Vietnamese diacritics in one file,
# needed because the narrative text arrives in Mandarin, Japanese and Vietnamese.
UNICODE_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"


def render_report_pdf(narrative_text: str, language: str, month: int, year: int) -> bytes:
    if not os.path.exists(UNICODE_FONT_PATH):
        raise FileNotFoundError(
            f"Unicode font not found at {UNICODE_FONT_PATH}. "
            "Required to render Mandarin/Japanese/Vietnamese text in the PDF."
        )

    colors = FLAG_COLORS[language]

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("UnicodeFont", "", UNICODE_FONT_PATH)

    pdf.set_fill_color(*colors["field"])
    pdf.rect(70, 15, 70, 45, style="F")
    pdf.set_fill_color(*colors["accent"])
    pdf.ellipse(95, 27.5, 20, 20, style="F")
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(70, 15, 70, 45)

    pdf.set_xy(0, 68)
    pdf.set_font("UnicodeFont", size=14)
    pdf.cell(0, 10, f"{COUNTRY_NAMES[language]} Regional Report - {month:02d}/{year}", align="C")

    pdf.set_xy(20, 90)
    pdf.set_font("UnicodeFont", size=12)
    pdf.multi_cell(170, 8, narrative_text)

    return bytes(pdf.output())
