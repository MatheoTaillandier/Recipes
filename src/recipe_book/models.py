"""Recipe data model: constants, validation/normalisation and quantity scaling."""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import datetime

# ── Choices offered in the UI ───────────────────────────────────────────────
SEASONS = {"spring": "🌸 Spring", "summer": "☀️ Summer", "autumn": "🍂 Autumn", "winter": "❄️ Winter"}
MEALS = {"breakfast": "🥐 Breakfast", "lunch": "🥗 Lunch", "dinner": "🌙 Dinner", "snack": "🍪 Snack"}
COURSES = {"starter": "🥣 Starter", "main": "🍲 Main course", "dessert": "🍰 Dessert"}
DIETS = {"vegan": "🥦 Vegan", "vegetarian": "🥕 Vegetarian", "pescatarian": "🐟 Pescatarian", "meat": "🍗 Meat"}
PRICES = {1: "€ Cheap", 2: "€€ Moderate", 3: "€€€ Expensive"}

UNITS = [
    "", "g", "kg", "ml", "cl", "dl", "l", "tsp", "tbsp", "cup", "pinch",
    "piece", "clove", "slice", "can", "bunch", "handful", "oz", "lb",
]

# Units whose amounts read better as kitchen fractions (½, ¼…) than decimals.
_FRACTION_UNITS = {"", "tsp", "tbsp", "cup", "pinch", "piece", "clove", "slice", "can",
                   "bunch", "handful", "pcs", "oz", "lb"}
_FRACTIONS = [(0.25, "¼"), (1 / 3, "⅓"), (0.5, "½"), (2 / 3, "⅔"), (0.75, "¾")]


def empty_recipe() -> dict:
    return {
        "id": "",
        "title": "",
        "description": "",
        "image": None,
        "servings": 4,
        "seasons": [],
        "meals": [],
        "course": "main",
        "diet": None,
        "prep_time": 0,
        "cook_time": 0,
        "price": None,
        "cost": None,
        "rating": 0,
        "ingredients": [],
        "steps": [],
        "notes": "",
        "created": None,
        "updated": None,
    }


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60] or "recipe"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _to_number(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return None if isinstance(value, float) and math.isnan(value) else float(value)
    try:
        return float(str(value).replace(",", ".").strip())
    except ValueError:
        return None


def _to_int(value, default: int = 0) -> int:
    number = _to_number(value)
    return default if number is None else int(round(number))


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return list(value)


def _pick(data: dict, *keys, default=None):
    for key in keys:
        if data.get(key) not in (None, "", []):
            return data[key]
    return default


def normalize(data: dict) -> dict:
    """Return a clean recipe dict from any supported shape (incl. the old app format)."""
    recipe = empty_recipe()
    recipe["id"] = str(data.get("id") or "")
    recipe["title"] = str(_pick(data, "title", "name", default="")).strip()
    recipe["description"] = str(_pick(data, "description", "desc", default="")).strip()
    recipe["image"] = data.get("image") or None
    recipe["servings"] = max(1, _to_int(_pick(data, "servings", "number_servings"), 4))

    seasons = [s.lower() for s in _as_list(_pick(data, "seasons", "season"))]
    recipe["seasons"] = [s for s in SEASONS if s in seasons]
    meals = [m.lower() for m in _as_list(data.get("meals"))]
    recipe["meals"] = [m for m in MEALS if m in meals]
    course = str(data.get("course") or "main").lower()
    recipe["course"] = {"desert": "dessert", "entree": "starter"}.get(course, course)
    if recipe["course"] not in COURSES:
        recipe["course"] = "main"
    diet = str(data.get("diet") or data.get("food_type") or "").lower()
    recipe["diet"] = diet if diet in DIETS else None

    recipe["prep_time"] = max(0, _to_int(data.get("prep_time")))
    recipe["cook_time"] = max(0, _to_int(data.get("cook_time")))
    price = _to_int(data.get("price"), 0)
    recipe["price"] = price if price in PRICES else None
    cost = _to_number(data.get("cost"))
    recipe["cost"] = cost if cost and cost > 0 else None
    recipe["rating"] = min(5, max(0, _to_int(_pick(data, "rating", "score"), 0)))

    ingredients = []
    for item in _as_list(data.get("ingredients")):
        if isinstance(item, str):
            from .importer import parse_ingredient_line  # local import avoids a cycle

            item = parse_ingredient_line(item)
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        quantity = _to_number(item.get("quantity"))
        ingredients.append({
            "quantity": quantity if quantity and quantity > 0 else None,
            "unit": str(item.get("unit") or "").strip(),
            "name": name,
        })
    recipe["ingredients"] = ingredients

    steps = data.get("steps") or data.get("instructions") or []
    if isinstance(steps, str):
        steps = steps.splitlines()
    recipe["steps"] = [str(s).strip() for s in steps if str(s).strip()]
    recipe["notes"] = str(data.get("notes") or "").strip()
    recipe["created"] = data.get("created")
    recipe["updated"] = data.get("updated")
    return recipe


# ── Scaling & display helpers ───────────────────────────────────────────────
def scale_factor(recipe: dict, people: int) -> float:
    return people / max(1, recipe.get("servings") or 1)


def format_quantity(quantity: float | None, unit: str = "") -> str:
    if quantity is None:
        return ""
    if unit.lower() in _FRACTION_UNITS:
        whole = math.floor(quantity)
        rest = quantity - whole
        if rest < 0.05:
            return str(whole) if whole else "a little"
        if rest > 0.95:
            return str(whole + 1)
        for value, symbol in _FRACTIONS:
            if abs(rest - value) < 0.05:
                return f"{whole}{symbol}" if whole else symbol
    if quantity >= 100:
        return str(int(round(quantity / 5) * 5))
    if quantity >= 10:
        return str(int(round(quantity)))
    return f"{quantity:.2f}".rstrip("0").rstrip(".")


def format_ingredient(ingredient: dict, factor: float = 1.0) -> str:
    quantity = ingredient.get("quantity")
    unit = ingredient.get("unit") or ""
    if quantity is None:
        return ingredient["name"]
    quantity *= factor
    if unit in ("g", "ml") and quantity >= 1000:
        quantity, unit = quantity / 1000, {"g": "kg", "ml": "l"}[unit]
    amount = format_quantity(quantity, unit)
    return " ".join(part for part in (amount, unit, ingredient["name"]) if part)


def format_minutes(minutes: int) -> str:
    if not minutes:
        return "—"
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours} h {mins:02d}"
    return f"{hours} h" if hours else f"{mins} min"


def total_time(recipe: dict) -> int:
    return (recipe.get("prep_time") or 0) + (recipe.get("cook_time") or 0)


def format_cost(cost: float) -> str:
    return f"{cost:.2f} €".replace(".00 €", " €")
