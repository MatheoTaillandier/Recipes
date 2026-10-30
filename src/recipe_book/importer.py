"""Read recipes from files: the app's own JSON export, web pages (schema.org) and plain text."""

from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path

from .models import normalize

_UNICODE_FRACTIONS = {"½": 0.5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": 0.25, "¾": 0.75, "⅕": 0.2,
                      "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875}

_UNIT_ALIASES = {
    "g": ["g", "gr", "gram", "grams", "gramme", "grammes"],
    "kg": ["kg", "kilo", "kilos", "kilogram", "kilograms"],
    "ml": ["ml", "millilitre", "millilitres", "milliliter", "milliliters"],
    "cl": ["cl", "centilitre", "centilitres"],
    "dl": ["dl"],
    "l": ["l", "litre", "litres", "liter", "liters"],
    "tsp": ["tsp", "tsps", "teaspoon", "teaspoons", "cac", "c.a.c", "c.à.c", "cc"],
    "tbsp": ["tbsp", "tbsps", "tbs", "tablespoon", "tablespoons", "cas", "c.a.s", "c.à.s", "cs"],
    "cup": ["cup", "cups", "tasse", "tasses"],
    "pinch": ["pinch", "pinches", "pincée", "pincées"],
    "piece": ["piece", "pieces", "pc", "pcs", "pièce", "pièces"],
    "clove": ["clove", "cloves", "gousse", "gousses"],
    "slice": ["slice", "slices", "tranche", "tranches"],
    "can": ["can", "cans", "tin", "tins", "boîte", "boîtes"],
    "bunch": ["bunch", "bunches", "botte", "bottes"],
    "handful": ["handful", "handfuls", "poignée", "poignées"],
    "oz": ["oz", "ounce", "ounces"],
    "lb": ["lb", "lbs", "pound", "pounds"],
}
_ALIAS_TO_UNIT = {alias: unit for unit, aliases in _UNIT_ALIASES.items() for alias in aliases}
_UNIT_PATTERN = "|".join(sorted((re.escape(a) for a in _ALIAS_TO_UNIT), key=len, reverse=True))

_NUMBER = r"\d+(?:[.,]\d+)?"
_QUANTITY = (
    rf"(?:(?P<whole>\d+)\s+(?P<num>\d+)/(?P<den>\d+)"  # 1 1/2
    rf"|(?P<fnum>\d+)/(?P<fden>\d+)"  # 1/2
    rf"|(?P<int>\d+)?\s*(?P<uni>[{''.join(_UNICODE_FRACTIONS)}])"  # 1½ or ½
    rf"|(?P<dec>{_NUMBER}))"  # 1.5 / 1,5
)
_INGREDIENT_RE = re.compile(
    rf"^\s*(?P<qty>{_QUANTITY})(?:\s*[-–à]\s*{_NUMBER})?\s*"
    rf"(?:(?P<unit>{_UNIT_PATTERN})\.?(?=\s|$))?\s*(?:(?:of|de|d')\s+)?(?P<name>.*)$",
    re.IGNORECASE,
)


def _quantity_from_match(m: re.Match) -> float:
    if m.group("whole"):
        return int(m.group("whole")) + int(m.group("num")) / max(1, int(m.group("den")))
    if m.group("fnum"):
        return int(m.group("fnum")) / max(1, int(m.group("fden")))
    if m.group("uni"):
        return int(m.group("int") or 0) + _UNICODE_FRACTIONS[m.group("uni")]
    return float(m.group("dec").replace(",", "."))


def parse_ingredient_line(line: str) -> dict:
    """'1 1/2 cups flour' -> {'quantity': 1.5, 'unit': 'cup', 'name': 'flour'}."""
    line = re.sub(r"^\s*(?:[-*•·▪◦]|\[\s?\])\s*", "", html.unescape(line)).strip()
    m = _INGREDIENT_RE.match(line)
    if not m or not m.group("name").strip():
        return {"quantity": None, "unit": "", "name": line}
    unit = m.group("unit")
    return {
        "quantity": _quantity_from_match(m),
        "unit": _ALIAS_TO_UNIT.get(unit.lower(), unit) if unit else "",
        "name": m.group("name").strip(" ,"),
    }


def parse_duration(value) -> int:
    """ISO 8601 ('PT1H30M') or free text ('1 h 30', '45 min') -> minutes."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().lower()
    m = re.fullmatch(r"p(?:(\d+)d)?t?(?:(\d+)h)?(?:(\d+)m)?(?:\d+s)?", text)
    if m and any(m.groups()):
        days, hours, mins = (int(g or 0) for g in m.groups())
        return days * 1440 + hours * 60 + mins
    hours = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:h|hr|hrs|hour|hours|heure|heures)\b\s*(\d+)?", text)
    mins = re.search(r"(\d+)\s*(?:m|min|mins|minute|minutes)\b", text)
    total = 0
    if hours:
        total += round(float(hours.group(1).replace(",", ".")) * 60) + int(hours.group(2) or 0)
    if mins and not (hours and hours.group(2)):
        total += int(mins.group(1))
    if not total and re.fullmatch(r"\d+", text):
        total = int(text)
    return total


def _first_int(value, default: int = 4) -> int:
    if isinstance(value, list):
        value = value[0] if value else None
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else default


# ── schema.org (recipe websites) ────────────────────────────────────────────
def _instruction_texts(value) -> list[str]:
    if isinstance(value, str):
        return [html.unescape(re.sub(r"<[^>]+>", "", s)).strip() for s in re.split(r"\n+", value) if s.strip()]
    steps = []
    for item in value or []:
        if isinstance(item, str):
            steps.extend(_instruction_texts(item))
        elif isinstance(item, dict):
            if item.get("itemListElement"):
                steps.extend(_instruction_texts(item["itemListElement"]))
            elif item.get("text") or item.get("name"):
                steps.extend(_instruction_texts(item.get("text") or item.get("name")))
    return steps


def from_schema_org(data: dict) -> dict:
    category = " ".join(data.get("recipeCategory") or []) if isinstance(data.get("recipeCategory"), list) \
        else str(data.get("recipeCategory") or "")
    category = category.lower()
    courses = [c for c, words in (("starter", ("starter", "appetizer", "entrée", "entree", "soup")),
                                  ("main", ("main", "dinner", "lunch")), ("dessert", ("dessert",)))
               if any(w in category for w in words)]
    keywords = str(data.get("keywords") or "").lower() + " " + category
    return normalize({
        "title": html.unescape(str(data.get("name") or "")),
        "description": html.unescape(str(data.get("description") or "")),
        "servings": _first_int(data.get("recipeYield")),
        "prep_time": parse_duration(data.get("prepTime")),
        "cook_time": parse_duration(data.get("cookTime")),
        "courses": courses,
        "meals": [m for m in ("breakfast", "lunch", "dinner", "snack") if m in keywords],
        "seasons": [s for s in ("spring", "summer", "autumn", "winter") if s in keywords],
        "ingredients": [parse_ingredient_line(str(i)) for i in data.get("recipeIngredient") or []],
        "steps": _instruction_texts(data.get("recipeInstructions")),
    })


def _find_schema_recipes(node) -> list[dict]:
    found = []
    if isinstance(node, list):
        for item in node:
            found.extend(_find_schema_recipes(item))
    elif isinstance(node, dict):
        kind = node.get("@type")
        kinds = kind if isinstance(kind, list) else [kind]
        if "Recipe" in kinds:
            found.append(node)
        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in node:
                found.extend(_find_schema_recipes(node[key]))
    return found


def _from_html(text: str) -> list[dict]:
    recipes = []
    for block in re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", text, re.S | re.I):
        try:
            recipes.extend(from_schema_org(r) for r in _find_schema_recipes(json.loads(block.strip())))
        except ValueError:
            continue
    return recipes


# ── Plain text / Markdown ───────────────────────────────────────────────────
_SECTION_WORDS = {
    "ingredients": ("ingredient", "ingrédient", "you will need", "shopping list"),
    "steps": ("instruction", "step", "method", "direction", "preparation", "préparation", "étape", "recette"),
    "notes": ("note", "tip", "astuce", "conseil"),
}


def _section_of(line: str) -> str | None:
    clean = re.sub(r"^[#*_\s]+|[#*_:\s]+$", "", line).lower()
    if not clean or len(clean) > 40:
        return None
    for section, words in _SECTION_WORDS.items():
        if any(clean.startswith(w) for w in words):
            return section
    return None


def from_text(text: str) -> dict:
    lines = [line.rstrip() for line in text.splitlines()]
    title, description, ingredients, steps, notes = "", [], [], [], []
    meta = {}
    section = "description"
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not title:
            title = re.sub(r"^#+\s*|^title\s*:\s*", "", line, flags=re.I).strip("*_ ")
            continue
        new_section = _section_of(line)
        if new_section:
            section = new_section
            continue
        meta_match = re.match(
            r"^[*_]*(serves|servings?|portions?|pour|people|yield|prep(?:aration)?\s*time|cook(?:ing)?\s*time"
            r"|temps de préparation|temps de cuisson)[*_]*\s*[:=-]?\s*(.+)$", line, re.I)
        if meta_match and section in ("description", "ingredients") and len(line) < 60:
            key, value = meta_match.group(1).lower(), meta_match.group(2)
            if "prep" in key or "préparation" in key:
                meta["prep_time"] = parse_duration(value)
            elif "cook" in key or "cuisson" in key:
                meta["cook_time"] = parse_duration(value)
            else:
                meta["servings"] = _first_int(value)
            continue
        if section == "description":
            description.append(line)
        elif section == "ingredients":
            ingredients.append(parse_ingredient_line(line))
        elif section == "steps":
            step = re.sub(r"^(?:\d+[.)]|step\s*\d+\s*[:.-]?|[-*•])\s*", "", line, flags=re.I)
            if step:
                steps.append(step)
        else:
            notes.append(re.sub(r"^[-*•]\s*", "", line))
    return normalize({
        "title": title,
        "description": " ".join(description),
        "ingredients": ingredients,
        "steps": steps,
        "notes": "\n".join(notes),
        **meta,
    })


# ── Entry point ─────────────────────────────────────────────────────────────
def _from_json(data) -> list[dict]:
    if isinstance(data, dict) and isinstance(data.get("recipes"), list):
        data = data["recipes"]
    items = data if isinstance(data, list) else [data]
    recipes = []
    for item in items:
        if not isinstance(item, dict):
            continue
        schema = _find_schema_recipes(item)
        if schema:
            recipes.extend(from_schema_org(r) for r in schema)
            continue
        recipe = normalize(item)
        if item.get("image_data"):
            recipe["image_data"] = item["image_data"]
        if recipe["title"]:
            recipe["id"] = ""  # imported recipes always get a fresh id
            recipes.append(recipe)
    return recipes


def parse_recipe_file(filename: str, content: bytes) -> list[dict]:
    """Return the recipes found in an uploaded file (possibly several, e.g. a backup)."""
    text = content.decode("utf-8-sig", errors="replace")
    suffix = Path(filename).suffix.lower()
    if suffix == ".json" or text.lstrip().startswith(("{", "[")):
        try:
            return _from_json(json.loads(text))
        except ValueError:
            if suffix == ".json":
                raise ValueError("This JSON file is damaged or not valid JSON.") from None
    if suffix in (".html", ".htm") or re.search(r"<html|<script", text[:5000], re.I):
        recipes = _from_html(text)
        if recipes:
            return recipes
        raise ValueError("No recipe was found in this web page.")
    recipe = from_text(text)
    return [recipe] if recipe["title"] else []


# ── Export ──────────────────────────────────────────────────────────────────
def export_recipes(recipes: list[dict], image_loader) -> bytes:
    """Serialise recipes (with their photo embedded) so they can be imported elsewhere."""
    out = []
    for recipe in recipes:
        item = {k: v for k, v in recipe.items() if k not in ("image",)}
        path = image_loader(recipe)
        if path:
            mime = path.suffix.lower().lstrip(".").replace("jpg", "jpeg")
            item["image_data"] = f"data:image/{mime};base64," + base64.b64encode(path.read_bytes()).decode()
        out.append(item)
    payload = out[0] if len(out) == 1 else {"recipes": out}
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def decode_image_data(data_url: str) -> tuple[str, bytes] | None:
    m = re.match(r"data:image/(\w+);base64,(.+)", data_url or "", re.S)
    if not m:
        return None
    try:
        return f"photo.{m.group(1).replace('jpeg', 'jpg')}", base64.b64decode(m.group(2))
    except ValueError:
        return None
