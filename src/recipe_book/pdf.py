"""Printable PDF version of a recipe, with amounts for a given number of people."""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from .models import (
    COURSES, DIETS, MEALS, PRICES, SEASONS, format_cost, format_ingredient, format_minutes,
    scale_factor, total_time,
)

FONTS_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
ACCENT = (200, 100, 43)  # same terracotta as the app theme
TEXT = (47, 38, 32)
MUTED = (122, 106, 92)

# The PDF fonts have no emoji: drop them (and the space after) from labels and user text.
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]+\\s?")


def _plain(text: str) -> str:
    return _EMOJI.sub("", text or "").strip()


class _RecipePDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Sans", size=8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"My Recipe Book · page {self.page_no()}", align="C")


def build_pdf(recipe: dict, people: int, image: Path | None = None) -> bytes:
    factor = scale_factor(recipe, people)
    pdf = _RecipePDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_font("Sans", "", str(FONTS_DIR / "DejaVuSans.ttf"))
    pdf.add_font("Sans", "B", str(FONTS_DIR / "DejaVuSans-Bold.ttf"))
    pdf.add_font("Serif", "B", str(FONTS_DIR / "DejaVuSerif-Bold.ttf"))
    pdf.add_page()
    width = pdf.epw

    # ── Title, photo and description ────────────────────────────────────────
    pdf.set_text_color(*TEXT)
    pdf.set_font("Serif", "B", 24)
    pdf.multi_cell(width, 11, _plain(recipe["title"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    if image:
        try:
            pdf.image(str(image), x=pdf.l_margin, w=width, h=70, keep_aspect_ratio=True)
            pdf.ln(3)
        except Exception:  # an unreadable photo should never block the PDF
            pass
    if recipe["description"]:
        pdf.set_font("Sans", size=11)
        pdf.multi_cell(width, 6, _plain(recipe["description"]), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    # Works with one part of the meal ("course") or several ("courses").
    courses = recipe.get("courses") or [recipe.get("course") or "main"]
    tags = [COURSES[c] for c in courses] + [MEALS[m] for m in recipe["meals"]]
    tags += [SEASONS[s] for s in recipe["seasons"]] or ["All year"]
    if recipe["diet"]:
        tags.append(DIETS[recipe["diet"]])
    if recipe["price"]:
        tags.append(PRICES[recipe["price"]])
    pdf.set_font("Sans", size=9)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(width, 5, "  ·  ".join(_plain(t) for t in tags), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Key facts ───────────────────────────────────────────────────────────
    facts = [("For", f"{people} {'person' if people == 1 else 'people'}"),
             ("Preparation", format_minutes(recipe["prep_time"])),
             ("Cooking", format_minutes(recipe["cook_time"])),
             ("Total", format_minutes(total_time(recipe)))]
    if recipe["cost"]:
        facts.append(("Cost", "≈ " + format_cost(recipe["cost"] * factor)))
    pdf.ln(3)
    box_w = width / len(facts)
    top = pdf.get_y()
    pdf.set_fill_color(247, 236, 225)
    pdf.rect(pdf.l_margin, top, width, 15, style="F")
    for n, (label, value) in enumerate(facts):
        x = pdf.l_margin + n * box_w
        pdf.set_xy(x, top + 2)
        pdf.set_font("Sans", size=8)
        pdf.set_text_color(*MUTED)
        pdf.cell(box_w, 4, label.upper(), align="C")
        pdf.set_xy(x, top + 7)
        pdf.set_font("Sans", "B", 11)
        pdf.set_text_color(*TEXT)
        pdf.cell(box_w, 6, value, align="C")
    pdf.set_y(top + 15)
    if people != recipe["servings"]:
        pdf.set_font("Sans", size=8)
        pdf.set_text_color(*MUTED)
        pdf.cell(width, 6, f"Amounts adjusted from the original recipe for {recipe['servings']}.",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def heading(text: str) -> None:
        pdf.ln(5)
        pdf.set_font("Serif", "B", 15)
        pdf.set_text_color(*TEXT)
        pdf.cell(width, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(*ACCENT)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 25, pdf.get_y())
        pdf.ln(3)

    # ── Ingredients & steps ─────────────────────────────────────────────────
    heading("Ingredients")
    pdf.set_font("Sans", size=11)
    pdf.set_text_color(*TEXT)
    for ingredient in recipe["ingredients"]:
        pdf.multi_cell(width, 6.5, "▢  " + _plain(format_ingredient(ingredient, factor)),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if not recipe["ingredients"]:
        pdf.cell(width, 6, "No ingredients listed.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    heading("Instructions")
    for n, step in enumerate(recipe["steps"], 1):
        pdf.set_font("Sans", "B", 11)
        pdf.set_text_color(*ACCENT)
        pdf.cell(9, 6.5, f"{n}.")
        pdf.set_font("Sans", size=11)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(width - 9, 6.5, _plain(step), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1.5)
    if not recipe["steps"]:
        pdf.set_font("Sans", size=11)
        pdf.cell(width, 6, "No instructions yet.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if recipe["notes"]:
        heading("Notes")
        pdf.set_font("Sans", size=10.5)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(width, 6, _plain(recipe["notes"]), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())
