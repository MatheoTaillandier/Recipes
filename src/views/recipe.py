import html

import streamlit as st

from recipe_book import importer, pdf, storage, ui
from recipe_book.models import (
    COURSES, DIETS, MEALS, PRICES, SEASONS, format_cost, format_ingredient, format_minutes,
    scale_factor, total_time,
)

recipe = storage.get_recipe(st.query_params.get("id", ""))
if recipe is None:
    st.warning("Cette recette est introuvable. Elle a peut-être été supprimée.", icon="🤷")
    st.page_link(ui.HOME, label="Retour à toutes les recettes", icon="⬅️")
    st.stop()


@st.dialog("Supprimer cette recette ?")
def confirm_delete():
    st.write(f"**{recipe['title']}** sera retirée de votre carnet de recettes. Cette action est définitive.")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Annuler"):
            st.rerun()
        if st.button("Supprimer", type="primary", icon="🗑️"):
            storage.delete_recipe(recipe["id"])
            ui.flash(f"« {recipe['title']} » a été supprimée", "🗑️")
            st.switch_page(ui.HOME)


def save_rating():
    value = st.session_state[f"rating_{recipe['id']}"]
    recipe["rating"] = 0 if value is None else value + 1
    storage.save_recipe(recipe)


# ── Action bar ──────────────────────────────────────────────────────────────
with st.container(horizontal=True, key="recipe_actions"):
    st.page_link(ui.HOME, label="Toutes les recettes", icon="⬅️")
    st.space("stretch")
    if st.button("Modifier", icon="✏️", type="primary"):
        st.switch_page(ui.EDITOR, query_params={"id": recipe["id"]})
    with st.popover("Télécharger", icon="💾"):
        people = st.session_state.people
        st.download_button(f"PDF — à imprimer ou à lire (pour {people} personne{'s' if people != 1 else ''})",
                           data=lambda: pdf.build_pdf(recipe, people, storage.image_path(recipe)),
                           file_name=f"{recipe['id']}.pdf", mime="application/pdf", icon="📄",
                           on_click="ignore", width="stretch")
        st.download_button("Fichier de recette (.json) — à partager ou à réimporter",
                           data=lambda: importer.export_recipes([recipe], storage.image_path),
                           file_name=f"{recipe['id']}.json", mime="application/json", icon="🗂️",
                           on_click="ignore", width="stretch")
    if st.button("Supprimer", icon="🗑️"):
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
    chips = [COURSES[c] for c in recipe["courses"]]
    chips += [MEALS[m] for m in recipe["meals"]]
    chips += [SEASONS[s] for s in recipe["seasons"]] or ["🗓️ Toute l'année"]
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
metric_cols[0].metric("Préparation", format_minutes(recipe["prep_time"]))
metric_cols[1].metric("Cuisson", format_minutes(recipe["cook_time"]))
metric_cols[2].metric("Temps total", format_minutes(total_time(recipe)))
if recipe["cost"]:
    metric_cols[3].metric(f"Coût pour {people}", format_cost(recipe["cost"] * factor),
                          help=f"≈ {format_cost(recipe['cost'] / recipe['servings'])} par personne")
else:
    metric_cols[3].metric("Prix", "€" * recipe["price"] if recipe["price"] else "—")

if people != recipe["servings"]:
    st.info(f"Quantités adaptées pour **{people}** "
            f"personne{'s' if people != 1 else ''} (la recette d'origine est pour {recipe['servings']}).",
            icon="⚖️")

st.divider()

# ── Ingredients & steps ─────────────────────────────────────────────────────
ing_col, steps_col = st.columns([2, 3], gap="large")
with ing_col:
    st.subheader("🧂 Ingrédients")
    if not recipe["ingredients"]:
        st.caption("Aucun ingrédient indiqué.")
    for n, ingredient in enumerate(recipe["ingredients"]):
        # Checkboxes double as a shopping / mise-en-place list.
        st.checkbox(format_ingredient(ingredient, factor), key=f"ing_{recipe['id']}_{n}")

with steps_col:
    st.subheader("👩‍🍳 Préparation")
    if not recipe["steps"]:
        st.caption("Pas encore d'étapes.")
    st.markdown("".join(
        f'<div class="rb-step"><div class="rb-step-num">{n}</div>'
        f'<div class="rb-step-text">{html.escape(step)}</div></div>'
        for n, step in enumerate(recipe["steps"], 1)
    ), unsafe_allow_html=True)
    if recipe["notes"]:
        st.subheader("📝 Notes")
        st.markdown(html.escape(recipe["notes"]).replace("\n", "  \n"))
