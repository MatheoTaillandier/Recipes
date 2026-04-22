import streamlit as st
import json

st.set_page_config(page_title="Recipe Book", page_icon="🍽️", layout="wide")

@st.cache_data
def load_recipes():
    with open("assets/data/recipes.json") as f:
        return json.load(f)

recipes = load_recipes()

EMOJI_TO_SEASON = { "☀️": "summer", "❄️": "winter", "🌸": "spring", "🍂": "autumn" }
EMOJI_TO_FOOD_TYPE = { "🥦": "vegan", "🥕": "vegetarian", "🐟": "pescatarian", "🍗": "meat" }
SEASON_TO_EMOJI = {v: k for k, v in EMOJI_TO_SEASON.items()}
FOOD_TYPE_TO_EMOJI = {v: k for k, v in EMOJI_TO_FOOD_TYPE.items()}
COLS_PER_ROW = 5

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🍽️ Recipe Book")
st.caption("Simple, seasonal dishes for every table")
st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
seasons = list(EMOJI_TO_SEASON.keys())
food_types = list(EMOJI_TO_FOOD_TYPE.keys())
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    season_filter = st.segmented_control("🌿 Season", ["All"] + seasons, default="All")
with col2:
    food_type_filter = st.segmented_control("🍲 Food type", ["All"] + food_types, default="All")
with col3:
    sort_by = st.selectbox("↕️ Sort by", ["Title", "Score ↓", "Servings"])

filtered = recipes if season_filter == "All" else [r for r in recipes if r["season"] == EMOJI_TO_SEASON.get(season_filter, "")]

if sort_by == "Title":
    filtered = sorted(filtered, key=lambda x: x["title"])
elif sort_by == "Score ↓":
    filtered = sorted(filtered, key=lambda x: x["score"], reverse=True)
elif sort_by == "Servings":
    filtered = sorted(filtered, key=lambda x: x["number_servings"])

st.caption(f"{len(filtered)} recipe{'s' if len(filtered) != 1 else ''} found")
st.divider()

# ── Grid of cards ─────────────────────────────────────────────────────────────
rows = [filtered[i:i+COLS_PER_ROW] for i in range(0, len(filtered), COLS_PER_ROW)]

for row in rows:
    cols = st.columns(COLS_PER_ROW, gap="medium")
    for col, recipe in zip(cols, row):
        season = recipe["season"]
        stars = "⭐" * recipe["score"]
        season_icon = SEASON_TO_EMOJI.get(season, "🌿")
        base_servings = recipe["number_servings"]

        with col:
            with st.container(border=True):
                col1_title, col2_title = st.columns([1, 1])

                col1_title.markdown(f"### {recipe['title']}")
                col2_title.markdown(
                    f"<h3 style='text-align: right;'>{season_icon}</h3>",
                    unsafe_allow_html=True
                )
                st.caption(recipe["desc"])
                st.feedback("stars", key=f"score_{recipe['id']}", default=recipe["score"], width="content")

                with st.expander("View recipe"):
                    servings = st.number_input(
                        "👤 Servings",
                        min_value=1,
                        max_value=50,
                        value=base_servings,
                        step=1,
                        key=f"servings_{recipe['id']}"
                    )
                    ratio = servings / base_servings

                    ing_col, step_col = st.columns(2)

                    with ing_col:
                        st.markdown("**🧂 Ingredients**")
                        for ing in recipe["ingredients"]:
                            scaled = ing["quantity"] * ratio
                            # Display as int if whole number, else round to 2 decimals
                            qty = int(scaled) if scaled == int(scaled) else round(scaled, 2)
                            st.write(f"- {qty} {ing['unit']} {ing['name']}")

                    with step_col:
                        st.markdown("**👨‍🍳 Steps**")
                        for i, step in enumerate(recipe["steps"], 1):
                            st.write(f"{i}. {step}")