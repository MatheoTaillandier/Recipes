import pandas as pd
import streamlit as st

from recipe_book import importer, storage, ui
from recipe_book.models import COURSES, DIETS, MEALS, PRICES, SEASONS, UNITS, empty_recipe, normalize

recipe_id = st.query_params.get("id", "")
draft = st.session_state.get("editor_draft")

if recipe_id:
    original = storage.get_recipe(recipe_id)
    if original is None:
        st.warning("This recipe could not be found. It may have been deleted.", icon="🤷")
        st.page_link(ui.HOME, label="Back to all recipes", icon="⬅️")
        st.stop()
    load_key = f"edit:{recipe_id}"
elif draft:
    original, load_key = draft, f"draft:{id(draft)}"
else:
    original, load_key = empty_recipe(), "new"


def load_form(recipe: dict) -> None:
    """Copy a recipe into the form widgets."""
    st.session_state.update({
        "ed_title": recipe["title"],
        "ed_description": recipe["description"],
        "ed_servings": recipe["servings"],
        "ed_course": recipe["course"],
        "ed_meals": recipe["meals"],
        "ed_seasons": recipe["seasons"],
        "ed_diet": recipe["diet"],
        "ed_prep": recipe["prep_time"],
        "ed_cook": recipe["cook_time"],
        "ed_price": recipe["price"],
        "ed_cost": recipe["cost"],
        "ed_steps": "\n".join(recipe["steps"]),
        "ed_notes": recipe["notes"],
        "ed_remove_image": False,
    })
    rows = recipe["ingredients"] or [{"quantity": None, "unit": "", "name": ""}]
    table = pd.DataFrame(rows, columns=["quantity", "unit", "name"])
    table["unit"] = table["unit"].where(table["unit"] != "", None)  # empty cells instead of a blank option
    st.session_state.ed_ingredients = table
    st.session_state.ed_version = st.session_state.get("ed_version", 0) + 1  # resets the table widget
    st.session_state.ed_loaded = load_key


if st.session_state.get("ed_loaded") != load_key:
    load_form(original)

is_new = not recipe_id
st.title("➕ New recipe" if is_new else f"✏️ Edit “{original['title']}”")
if draft and is_new:
    st.success("The recipe was read from your file. Check the details below, then click **Save recipe**.",
               icon="📥")
elif is_new:
    with st.container(horizontal=True, vertical_alignment="center"):
        st.caption("Fill in what you know — only the name is required. You can always come back and edit it.")
        st.page_link(ui.IMPORT, label="Have a recipe file? Import it", icon="📥")

# ── General information ─────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("General")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.text_input("Recipe name *", key="ed_title", placeholder="e.g. Grandma's apple pie")
        st.text_area("Short description", key="ed_description", height=90,
                     placeholder="What makes this dish special?")
    with right:
        current_image = storage.image_path(original) if not draft else None
        draft_image = importer.decode_image_data(original.get("image_data", "")) if draft else None
        if current_image or draft_image:
            st.image(str(current_image) if current_image else draft_image[1], width=220)
            st.checkbox("Remove this photo", key="ed_remove_image")
        upload = st.file_uploader("Photo (optional)", type=storage.IMAGE_TYPES, key=f"ed_photo_{load_key}",
                                  help="A picture of the finished dish, shown on the recipe card.")

with st.container(border=True):
    st.subheader("Details")
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.number_input("👥 This recipe is for how many people? *", min_value=1, max_value=100, step=1,
                        key="ed_servings",
                        help="The quantities you enter below are for this number of people. The app "
                             "recalculates them automatically when you cook for more or fewer people.")
        st.number_input("🔪 Preparation time (minutes)", min_value=0, max_value=2000, step=5, key="ed_prep")
        st.number_input("🔥 Cooking time (minutes)", min_value=0, max_value=2000, step=5, key="ed_cook")
    with c2:
        st.segmented_control("Part of the meal *", list(COURSES), format_func=COURSES.get, key="ed_course",
                             required=True)
        st.pills("Meal", list(MEALS), format_func=MEALS.get, selection_mode="multi", key="ed_meals",
                 help="When would you eat this? Pick as many as you like.")
        st.pills("Season", list(SEASONS), format_func=SEASONS.get, selection_mode="multi", key="ed_seasons",
                 help="Leave empty if this recipe works all year round.")
    with c3:
        st.segmented_control("Price", list(PRICES), format_func=PRICES.get, key="ed_price")
        st.number_input("💶 Estimated cost in € (optional)", min_value=0.0, max_value=10000.0, step=0.5,
                        key="ed_cost", format="%.2f",
                        help="Total cost for the number of people above. It is scaled like the ingredients.")
        st.pills("Diet", list(DIETS), format_func=DIETS.get, key="ed_diet")

# ── Ingredients ─────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🧂 Ingredients")
    st.caption(f"Quantities for **{st.session_state.ed_servings}** "
               f"{'person' if st.session_state.ed_servings == 1 else 'people'}. Click a cell to type, "
               "use the **+** below the table to add a line, select a row and press the bin to remove it. "
               "Leave the quantity empty for things like “salt, to taste”.")
    units = list(dict.fromkeys([u for u in UNITS if u] + [u for u in st.session_state.ed_ingredients["unit"] if isinstance(u, str) and u]))
    ingredients = st.data_editor(
        st.session_state.ed_ingredients,
        key=f"ed_table_{st.session_state.ed_version}",
        num_rows="dynamic",
        hide_index=True,
        placeholder="",
        width="stretch",
        column_order=["quantity", "unit", "name"],
        column_config={
            "quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=0.01, format="%g",
                                                      width="small"),
            "unit": st.column_config.SelectboxColumn("Unit", options=units, width="small",
                                                     help="Leave empty for items counted as-is (2 eggs)."),
            "name": st.column_config.TextColumn("Ingredient", width="large"),
        },
    )
    with st.expander("✍️ Paste a list of ingredients instead"):
        pasted = st.text_area("One ingredient per line, e.g. “200 g flour” or “2 eggs”", key="ed_paste",
                              height=150)
        if st.button("Add these ingredients to the table", disabled=not pasted.strip()):
            parsed = [importer.parse_ingredient_line(line) for line in pasted.splitlines() if line.strip()]
            current = ingredients.dropna(subset=["name"])
            current = current[current["name"].astype(str).str.strip() != ""]
            added = pd.DataFrame(parsed)
            added["unit"] = added["unit"].where(added["unit"] != "", None)
            st.session_state.ed_ingredients = pd.concat([current, added], ignore_index=True)
            st.session_state.ed_version += 1
            del st.session_state["ed_paste"]
            st.rerun()

# ── Instructions ────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("👩‍🍳 Instructions")
    st.text_area("Write one step per line — they will be numbered automatically.", key="ed_steps", height=220,
                 placeholder="Preheat the oven to 180 °C.\nMix the flour and the sugar.\nBake for 30 minutes.")
    st.text_area("📝 Notes (optional)", key="ed_notes", height=90,
                 placeholder="Tips, variations, wine pairing…")


# ── Save ────────────────────────────────────────────────────────────────────
def collect() -> dict:
    rows = []
    for row in ingredients.to_dict("records"):
        name = str(row.get("name") or "").strip()
        if name and name.lower() != "nan":
            unit = row.get("unit")
            rows.append({"quantity": row.get("quantity"), "unit": unit if isinstance(unit, str) else "",
                         "name": name})
    recipe = dict(original)
    recipe.update({
        "id": recipe_id,
        "title": st.session_state.ed_title.strip(),
        "description": st.session_state.ed_description,
        "servings": st.session_state.ed_servings,
        "course": st.session_state.ed_course or "main",
        "meals": st.session_state.ed_meals,
        "seasons": st.session_state.ed_seasons,
        "diet": st.session_state.ed_diet,
        "prep_time": st.session_state.ed_prep,
        "cook_time": st.session_state.ed_cook,
        "price": st.session_state.ed_price,
        "cost": st.session_state.ed_cost,
        "ingredients": rows,
        "steps": st.session_state.ed_steps.splitlines(),
        "notes": st.session_state.ed_notes,
    })
    return normalize(recipe)


with st.container(horizontal=True, horizontal_alignment="right", key="editor_actions"):
    cancel = st.button("Cancel", icon="✖️")
    save = st.button("Save recipe", icon="💾", type="primary")

if cancel:
    st.session_state.pop("editor_draft", None)
    if recipe_id:
        st.switch_page(ui.RECIPE, query_params={"id": recipe_id})
    st.switch_page(ui.HOME)

if save:
    recipe = collect()
    if not recipe["title"]:
        st.error("Please give your recipe a name (at the top of the page).", icon="✋")
        st.stop()
    image_data = original.get("image_data") if draft else None
    recipe.pop("image_data", None)
    if draft:
        recipe["image"] = None  # an imported recipe never points to someone else's photo file
    saved = storage.save_recipe(recipe)
    if upload is not None or st.session_state.ed_remove_image:
        storage.remove_image(saved)
        saved["image"] = None
    if upload is not None:
        saved["image"] = storage.store_image(saved["id"], upload.name, upload.getvalue())
    elif image_data and not st.session_state.ed_remove_image:
        decoded = importer.decode_image_data(image_data)
        if decoded:
            saved["image"] = storage.store_image(saved["id"], *decoded)
    storage.save_recipe(saved)
    st.session_state.pop("editor_draft", None)
    st.session_state.pop("ed_loaded", None)
    ui.flash(f"“{saved['title']}” was saved")
    st.switch_page(ui.RECIPE, query_params={"id": saved["id"]})
