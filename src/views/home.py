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
    search = st.text_input("🔎 Search", placeholder="Recipe name or ingredient, e.g. “carrot”",
                           key="search")
with top_mid:
    sort_by = st.selectbox("↕️ Sort by",
                           ["Name", "Best rated", "Quickest", "Cheapest", "Newest", "🎲 Random"],
                           key="sort_by")
with top_right:
    people = ui.people_input("people_home")

with st.container(horizontal=True, gap="medium", key="filter_row"):
    course_filter = st.pills("Course", list(COURSES), format_func=COURSES.get, selection_mode="multi",
                             key="f_course")
    meal_filter = st.pills("Meal", list(MEALS), format_func=MEALS.get, selection_mode="multi", key="f_meal")
    season_filter = st.pills("Season", list(SEASONS), format_func=SEASONS.get, selection_mode="multi",
                             key="f_season")
    diet_filter = st.pills("Diet", list(DIETS), format_func=DIETS.get, selection_mode="multi", key="f_diet")
    price_filter = st.pills("Price", list(PRICES), format_func=PRICES.get, selection_mode="multi",
                            key="f_price")
    max_time = st.slider("Ready in at most (minutes)", 0, 240, 240, step=5, key="f_time", width=260,
                         help="Preparation + cooking time. Leave at 240 to show everything.")

def matches(recipe: dict) -> bool:
    if search:
        needle = search.lower().strip()
        haystack = [recipe["title"], recipe["description"], *(i["name"] for i in recipe["ingredients"])]
        if not any(needle in text.lower() for text in haystack):
            return False
    if course_filter and recipe["course"] not in course_filter:
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
    "Name": lambda r: r["title"].lower(),
    "Best rated": lambda r: -r["rating"],
    "Quickest": lambda r: total_time(r) or 10_000,
    "Cheapest": lambda r: (r["price"] or 9, r["cost"] or 10_000),
    "Newest": lambda r: "".join(chr(255 - ord(c)) for c in (r["created"] or "")),
}
if sort_by == "🎲 Random":
    # Keep the same order while other settings change; the Shuffle button picks a new one.
    st.session_state.setdefault("shuffle_seed", random.random())
    filtered.sort(key=sort_keys["Name"])
    random.Random(st.session_state.shuffle_seed).shuffle(filtered)
else:
    filtered.sort(key=sort_keys[sort_by])

# ── Results ─────────────────────────────────────────────────────────────────
if not recipes:
    st.markdown('<div class="rb-empty"><div>📖</div><h3>Your recipe book is empty</h3>'
                '<p>Add your first recipe, or import one from a file.</p></div>', unsafe_allow_html=True)
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button("Add a recipe", icon="➕", type="primary", key="empty_add"):
            st.switch_page(ui.EDITOR)
        st.page_link(ui.IMPORT, label="Import a recipe file", icon="📥")
    st.stop()

with st.container(horizontal=True, vertical_alignment="center"):
    st.caption(f"{len(filtered)} of {len(recipes)} recipe{'s' if len(recipes) != 1 else ''} · "
               f"quantities shown for **{people} {'person' if people == 1 else 'people'}**")
    if sort_by == "🎲 Random":
        st.space("stretch")
        if st.button("Shuffle", icon="🎲", key="shuffle"):
            st.session_state.shuffle_seed = random.random()
            st.rerun()

if not filtered:
    st.markdown('<div class="rb-empty"><div>🔍</div><h3>No recipe matches these filters</h3>'
                '<p>Try removing a filter or searching for something else.</p></div>', unsafe_allow_html=True)
    st.stop()


def card(recipe: dict) -> None:
    factor = scale_factor(recipe, people)
    with st.container(border=True):
        image = storage.image_path(recipe)
        if image:
            st.image(str(image), width="stretch")
        else:
            st.markdown(f'<div class="rb-placeholder">{COURSE_EMOJI[recipe["course"]]}</div>',
                        unsafe_allow_html=True)
        st.markdown(f'<p class="rb-card-title">{html.escape(recipe["title"])}</p>'
                    f'<div class="rb-card-desc">{html.escape(recipe["description"]) or "&nbsp;"}</div>',
                    unsafe_allow_html=True)
        meta = [COURSES[recipe["course"]]]
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
        with st.expander(f"🧂 Ingredients for {people}"):
            lines = [f"- {format_ingredient(i, factor)}" for i in recipe["ingredients"]]
            st.markdown("\n".join(lines) or "_No ingredients yet_")
        st.page_link(ui.RECIPE, label="Open recipe", icon="👉", query_params={"id": recipe["id"]},
                     width="stretch")


for start in range(0, len(filtered), COLUMNS):
    cols = st.columns(COLUMNS, gap="medium")
    for col, recipe in zip(cols, filtered[start:start + COLUMNS]):
        with col:
            card(recipe)
