import html

import streamlit as st

from recipe_book import importer, pdf, storage, ui
from recipe_book.models import (
    COURSES, DIETS, MEALS, PRICES, SEASONS, format_cost, format_ingredient, format_minutes,
    scale_factor, total_time,
)

recipe = storage.get_recipe(st.query_params.get("id", ""))
if recipe is None:
    st.warning("This recipe could not be found. It may have been deleted.", icon="🤷")
    st.page_link(ui.HOME, label="Back to all recipes", icon="⬅️")
    st.stop()


@st.dialog("Delete this recipe?")
def confirm_delete():
    st.write(f"**{recipe['title']}** will be removed from your recipe book. This cannot be undone.")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancel"):
            st.rerun()
        if st.button("Delete", type="primary", icon="🗑️"):
            storage.delete_recipe(recipe["id"])
            ui.flash(f"“{recipe['title']}” was deleted", "🗑️")
            st.switch_page(ui.HOME)


def save_rating():
    value = st.session_state[f"rating_{recipe['id']}"]
    recipe["rating"] = 0 if value is None else value + 1
    storage.save_recipe(recipe)


# ── Action bar ──────────────────────────────────────────────────────────────
with st.container(horizontal=True, key="recipe_actions"):
    st.page_link(ui.HOME, label="All recipes", icon="⬅️")
    st.space("stretch")
    if st.button("Edit", icon="✏️", type="primary"):
        st.switch_page(ui.EDITOR, query_params={"id": recipe["id"]})
    with st.popover("Download", icon="💾"):
        people = st.session_state.people
        st.download_button(f"PDF — to print or read (for {people} {'person' if people == 1 else 'people'})",
                           data=lambda: pdf.build_pdf(recipe, people, storage.image_path(recipe)),
                           file_name=f"{recipe['id']}.pdf", mime="application/pdf", icon="📄",
                           on_click="ignore", width="stretch")
        st.download_button("Recipe file (.json) — to share or import again",
                           data=lambda: importer.export_recipes([recipe], storage.image_path),
                           file_name=f"{recipe['id']}.json", mime="application/json", icon="🗂️",
                           on_click="ignore", width="stretch")
    if st.button("Delete", icon="🗑️"):
        confirm_delete()

# ── Header ──────────────────────────────────────────────────────────────────
image = storage.image_path(recipe)
if image:
    text_col, image_col = st.columns([3, 2], gap="large")
else:
    text_col, image_col = st.container(), None

with text_col:
    st.title(recipe["title"])
    if recipe["description"]:
        st.markdown(f"<p style='font-size:1.1rem'>{html.escape(recipe['description'])}</p>",
                    unsafe_allow_html=True)
    chips = [COURSES[recipe["course"]]]
    chips += [MEALS[m] for m in recipe["meals"]]
    chips += [SEASONS[s] for s in recipe["seasons"]] or ["🗓️ All year"]
    if recipe["diet"]:
        chips.append(DIETS[recipe["diet"]])
    if recipe["price"]:
        chips.append(PRICES[recipe["price"]])
    st.markdown("".join(f'<span class="rb-chip">{c}</span>' for c in chips), unsafe_allow_html=True)
    st.feedback("stars", key=f"rating_{recipe['id']}", on_change=save_rating,
                default=recipe["rating"] - 1 if recipe["rating"] else None)

if image_col:
    with image_col:
        st.image(str(image), width="stretch")

people_col, *metric_cols = st.columns([1.3, 1, 1, 1, 1], vertical_alignment="bottom")
with people_col:
    people = ui.people_input("people_recipe")
factor = scale_factor(recipe, people)
metric_cols[0].metric("Preparation", format_minutes(recipe["prep_time"]))
metric_cols[1].metric("Cooking", format_minutes(recipe["cook_time"]))
metric_cols[2].metric("Total time", format_minutes(total_time(recipe)))
if recipe["cost"]:
    metric_cols[3].metric(f"Cost for {people}", format_cost(recipe["cost"] * factor),
                          help=f"≈ {format_cost(recipe['cost'] / recipe['servings'])} per person")
else:
    metric_cols[3].metric("Price", "€" * recipe["price"] if recipe["price"] else "—")

if people != recipe["servings"]:
    st.info(f"Amounts adjusted for **{people}** "
            f"{'person' if people == 1 else 'people'} (the original recipe is for {recipe['servings']}).",
            icon="⚖️")

st.divider()

# ── Ingredients & steps ─────────────────────────────────────────────────────
ing_col, steps_col = st.columns([2, 3], gap="large")
with ing_col:
    st.subheader("🧂 Ingredients")
    if not recipe["ingredients"]:
        st.caption("No ingredients listed.")
    for n, ingredient in enumerate(recipe["ingredients"]):
        # Checkboxes double as a shopping / mise-en-place list.
        st.checkbox(format_ingredient(ingredient, factor), key=f"ing_{recipe['id']}_{n}")

with steps_col:
    st.subheader("👩‍🍳 Instructions")
    if not recipe["steps"]:
        st.caption("No instructions yet.")
    st.markdown("".join(
        f'<div class="rb-step"><div class="rb-step-num">{n}</div>'
        f'<div class="rb-step-text">{html.escape(step)}</div></div>'
        for n, step in enumerate(recipe["steps"], 1)
    ), unsafe_allow_html=True)
    if recipe["notes"]:
        st.subheader("📝 Notes")
        st.markdown(html.escape(recipe["notes"]).replace("\n", "  \n"))
