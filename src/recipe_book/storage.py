"""Local storage: one JSON file per recipe inside a git-ignored folder."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .models import normalize, now_iso, slugify

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("RECIPE_BOOK_DATA", PROJECT_ROOT / "my_recipes"))
IMAGES_DIR = DATA_DIR / "images"
SETTINGS_FILE = DATA_DIR / "_settings.json"  # leading "_" can never clash with a recipe id
SAMPLES_DIR = PROJECT_ROOT / "assets" / "sample_recipes"
SAMPLE_IMAGES_DIR = PROJECT_ROOT / "assets" / "images"

IMAGE_TYPES = ["jpg", "jpeg", "png", "webp", "gif"]


def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def ensure_data_dir() -> None:
    """Create the data folder; on the very first run, add a few sample recipes."""
    if DATA_DIR.exists():
        IMAGES_DIR.mkdir(exist_ok=True)
        return
    IMAGES_DIR.mkdir(parents=True)
    for sample in sorted(SAMPLES_DIR.glob("*.json")):
        recipe = normalize(json.loads(sample.read_text(encoding="utf-8")))
        if recipe["image"] and (SAMPLE_IMAGES_DIR / recipe["image"]).exists():
            shutil.copy(SAMPLE_IMAGES_DIR / recipe["image"], IMAGES_DIR / recipe["image"])
        else:
            recipe["image"] = None
        save_recipe(recipe)


def load_recipes() -> list[dict]:
    ensure_data_dir()
    recipes = []
    for path in DATA_DIR.glob("*.json"):
        if path == SETTINGS_FILE:
            continue
        try:
            recipe = normalize(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue  # skip unreadable files rather than breaking the whole book
        recipe["id"] = path.stem
        recipes.append(recipe)
    return sorted(recipes, key=lambda r: r["title"].lower())


def get_recipe(recipe_id: str) -> dict | None:
    if not recipe_id:
        return None
    path = DATA_DIR / f"{slugify(recipe_id)}.json"
    if not path.exists():
        return None
    recipe = normalize(json.loads(path.read_text(encoding="utf-8")))
    recipe["id"] = path.stem
    return recipe


def _unique_id(title: str) -> str:
    base = slugify(title)
    candidate, n = base, 2
    while (DATA_DIR / f"{candidate}.json").exists():
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def save_recipe(recipe: dict) -> dict:
    """Create or update a recipe and return the saved version (with its id)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    recipe = normalize(recipe)
    if not recipe["id"] or not (DATA_DIR / f"{recipe['id']}.json").exists():
        recipe["id"] = _unique_id(recipe["title"] or "recipe")
        recipe["created"] = recipe["created"] or now_iso()
    recipe["updated"] = now_iso()
    _write_json(DATA_DIR / f"{recipe['id']}.json", recipe)
    return recipe


def duplicate_key(recipe: dict) -> str:
    """Two recipes are the same if their names match, ignoring case, accents and punctuation."""
    return slugify(recipe.get("title") or "")


def find_duplicate(recipe: dict, recipes: list[dict]) -> dict | None:
    key = duplicate_key(recipe)
    return next((r for r in recipes if duplicate_key(r) == key), None)


def save_imported(recipe: dict, replace: dict | None = None) -> dict:
    """Save an imported recipe (and its embedded photo), optionally over an existing one."""
    from .importer import decode_image_data  # local import: importer is optional for storage

    recipe = dict(recipe)
    decoded = decode_image_data(recipe.pop("image_data", None) or "")
    if replace:
        recipe.update(id=replace["id"], created=replace["created"], image=replace["image"])
        if not recipe["rating"]:
            recipe["rating"] = replace["rating"]
    else:
        recipe.update(id="", image=None)
    saved = save_recipe(recipe)
    if decoded:
        remove_image(saved)
        saved["image"] = store_image(saved["id"], *decoded)
        saved = save_recipe(saved)
    return saved


def delete_recipe(recipe_id: str) -> None:
    recipe = get_recipe(recipe_id)
    if recipe is None:
        return
    if recipe["image"]:
        (IMAGES_DIR / recipe["image"]).unlink(missing_ok=True)
    (DATA_DIR / f"{recipe['id']}.json").unlink(missing_ok=True)


def image_path(recipe: dict) -> Path | None:
    if not recipe.get("image"):
        return None
    path = IMAGES_DIR / recipe["image"]
    return path if path.exists() else None


def store_image(recipe_id: str, filename: str, content: bytes) -> str:
    """Save an uploaded photo for a recipe and return its file name."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix.lower().lstrip(".") or "jpg"
    for old in IMAGES_DIR.glob(f"{recipe_id}.*"):
        old.unlink()
    name = f"{recipe_id}.{ext}"
    (IMAGES_DIR / name).write_bytes(content)
    return name


def remove_image(recipe: dict) -> None:
    if recipe.get("image"):
        (IMAGES_DIR / recipe["image"]).unlink(missing_ok=True)


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(settings: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(SETTINGS_FILE, settings)
