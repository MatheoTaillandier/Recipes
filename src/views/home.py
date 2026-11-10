import html
import random

import streamlit as st

from recipe_book import storage, ui
from recipe_book.models import (
    COURSES, DIETS, MEALS, PRICES, SEASONS, format_cost, format_ingredient, format_minutes,
    scale_factor, total_time,
)

COURSE_EMOJI = {"starter": "🥣", "main": "🍲", "dessert": "🍰"}
COLUMNS = 3

recipes = storage.load_recipes()

# ── Filters ─────────────────────────────────────────────────────────────────
top_left, top_mid, top_right = st.columns([3, 1.3, 1.2], vertical_alignment="bottom")
with top_left:
    search = st.text_input("🔎 Rechercher", placeholder="Nom de recette ou ingrédient, ex. « carotte »",
                           key="search")
with top_mid:
    sort_by = st.selectbox("↕️ Trier par",
                           ["Nom", "Mieux notées", "Plus rapides", "Moins chères", "Plus récentes", "🎲 Au hasard"],
                           key="sort_by")
with top_right:
    people = ui.people_input("people_home")

with st.container(horizontal=True, gap="medium", key="filter_row"):
    course_filter = st.pills("Partie du repas", list(COURSES), format_func=COURSES.get, selection_mode="multi",
                             key="f_course")
    meal_filter = st.pills("Repas", list(MEALS), format_func=MEALS.get, selection_mode="multi", key="f_meal")
    season_filter = st.pills("Saison", list(SEASONS), format_func=SEASONS.get, selection_mode="multi",
                             key="f_season")
    diet_filter = st.pills("Régime", list(DIETS), format_func=DIETS.get, selection_mode="multi", key="f_diet")
    price_filter = st.pills("Prix", list(PRICES), format_func=PRICES.get, selection_mode="multi",
                            key="f_price")
    max_time = st.slider("Prêt en moins de (minutes)", 0, 240, 240, step=5, key="f_time", width=260,
                         help="Préparation + cuisson. Laissez sur 240 pour tout afficher.")

def matches(recipe: dict) -> bool:
    if search:
        needle = search.lower().strip()
        haystack = [recipe["title"], recipe["description"], *(i["name"] for i in recipe["ingredients"])]
        if not any(needle in text.lower() for text in haystack):
            return False
    if course_filter and not set(course_filter) & set(recipe["courses"]):
        return False
    if meal_filter and not set(meal_filter) & set(recipe["meals"]):
        return False
    # A recipe without seasons is good all year round.
    if season_filter and recipe["seasons"] and not set(season_filter) & set(recipe["seasons"]):
        return False
    if diet_filter and recipe["diet"] not in diet_filter:
        return False
    if price_filter and recipe["price"] not in price_filter:
        return False
    if max_time < 240 and total_time(recipe) > max_time:
        return False
    return True


filtered = [r for r in recipes if matches(r)]
sort_keys = {
    "Nom": lambda r: r["title"].lower(),
    "Mieux notées": lambda r: -r["rating"],
    "Plus rapides": lambda r: total_time(r) or 10_000,
    "Moins chères": lambda r: (r["price"] or 9, r["cost"] or 10_000),
    "Plus récentes": lambda r: "".join(chr(255 - ord(c)) for c in (r["created"] or "")),
}
if sort_by == "🎲 Au hasard":
    # Keep the same order while other settings change; the Shuffle button picks a new one.
    st.session_state.setdefault("shuffle_seed", random.random())
    filtered.sort(key=sort_keys["Nom"])
    random.Random(st.session_state.shuffle_seed).shuffle(filtered)
else:
    filtered.sort(key=sort_keys[sort_by])

# ── Results ─────────────────────────────────────────────────────────────────
if not recipes:
    st.markdown('<div class="rb-empty"><div>📖</div><h3>Votre carnet de recettes est vide</h3>'
                '<p>Ajoutez votre première recette, ou importez-en une depuis un fichier.</p></div>',
                unsafe_allow_html=True)
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button("Ajouter une recette", icon="➕", type="primary", key="empty_add"):
            st.switch_page(ui.EDITOR)
        st.page_link(ui.IMPORT, label="Importer un fichier de recette", icon="📥")
    st.stop()

with st.container(horizontal=True, vertical_alignment="center"):
    st.caption(f"{len(filtered)} sur {len(recipes)} recette{'s' if len(recipes) != 1 else ''} · "
               f"quantités pour **{people} personne{'s' if people != 1 else ''}**")
    if sort_by == "🎲 Au hasard":
        st.space("stretch")
        if st.button("Mélanger", icon="🎲", key="shuffle"):
            st.session_state.shuffle_seed = random.random()
            st.rerun()

if not filtered:
    st.markdown('<div class="rb-empty"><div>🔍</div><h3>Aucune recette ne correspond à ces filtres</h3>'
                '<p>Essayez de retirer un filtre ou de chercher autre chose.</p></div>', unsafe_allow_html=True)
    st.stop()


def card(recipe: dict) -> None:
    factor = scale_factor(recipe, people)
    # The "rb-card" key lets the CSS stretch the recipe link over the whole box (see ui.CSS).
    with st.container(border=True, key=f"rb-card-{recipe['id']}"):
        image = storage.image_path(recipe)
        if image:
            st.image(str(image), width="stretch")
        else:
            st.markdown(f'<div class="rb-placeholder">{COURSE_EMOJI[recipe["courses"][0]]}</div>',
                        unsafe_allow_html=True)
        st.markdown(f'<p class="rb-card-title">{html.escape(recipe["title"])}</p>'
                    f'<div class="rb-card-desc">{html.escape(recipe["description"]) or "&nbsp;"}</div>',
                    unsafe_allow_html=True)
        meta = [" · ".join(COURSES[c] for c in recipe["courses"])]
        if total_time(recipe):
            meta.append(f"⏱️ {format_minutes(total_time(recipe))}")
        if recipe["cost"]:
            meta.append(f"💶 ≈ {format_cost(recipe['cost'] * factor)}")
        elif recipe["price"]:
            meta.append("💶 " + "€" * recipe["price"])
        if recipe["rating"]:
            meta.append("⭐" * recipe["rating"])
        st.markdown('<div class="rb-meta">' + "".join(f"<span>{m}</span>" for m in meta) + "</div>",
                    unsafe_allow_html=True)
        with st.expander(f"🧂 Ingrédients pour {people}"):
            lines = [f"- {format_ingredient(i, factor)}" for i in recipe["ingredients"]]
            st.markdown("\n".join(lines) or "_Pas encore d'ingrédients_")
        st.page_link(ui.RECIPE, label=f"Ouvrir {recipe['title']}", query_params={"id": recipe["id"]},
                     width="stretch")


for start in range(0, len(filtered), COLUMNS):
    cols = st.columns(COLUMNS, gap="medium")
    for col, recipe in zip(cols, filtered[start:start + COLUMNS]):
        with col:
            card(recipe)
