import json
from pathlib import Path

import streamlit as st


@st.dialog("Add eaters", width="large")
def add_eater_dialog():
    profiles = st.session_state.profiles

    # Initialize temporary selection with currently active eaters
    if "selected_profiles" not in st.session_state:
        st.session_state.selected_profiles = (
            st.session_state.eaters.copy()
        )

    st.write("Select the people who are eating:")

    PROFILE_COLS = 4
    profile_items = list(profiles.items())

    # ── Profile cards ────────────────────────────────────────────────
    for i in range(0, len(profile_items), PROFILE_COLS):
        row = profile_items[i:i + PROFILE_COLS]
        cols = st.columns(PROFILE_COLS, gap="small")

        for col, (profile_name, profile) in zip(cols, row):
            with col:

                selected = (
                    profile_name
                    in st.session_state.selected_profiles
                )

                # Selected profile
                if selected:
                    with st.container(border=True):
                        st.success(f"👤 {profile_name}")
                        if st.button(
                            "Deselect",
                            key=f"profile_{profile_name}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_profiles.remove(
                                profile_name
                            )
                            st.rerun()

                # Unselected profile
                else:
                    with st.container(border=True):
                        st.write(f"👤 {profile_name}")

                        if st.button(
                            "Select",
                            key=f"profile_{profile_name}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_profiles.append(
                                profile_name
                            )
                            st.rerun()

    st.divider()

    # ── Done button ─────────────────────────────────────────────────
    if st.button(
        f"Done ({len(st.session_state.selected_profiles)} selected)",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.eaters = (
            st.session_state.selected_profiles.copy()
        )

        del st.session_state.selected_profiles

        st.session_state.show_add_eater_dialog = False

        st.rerun()

def load_recipes():
    with open("assets/data/recipes.json") as f:
        return json.load(f)

def load_profiles():
    profiles_dir = Path("assets/data/profiles")

    profiles = {}

    for json_file in profiles_dir.glob("*.json"):
        with open(json_file) as f:
            profiles[json_file.stem] = json.load(f)

    return profiles
# ── Variables ───────────────────────────────────────────────────────────────
if "profile" not in st.session_state:
    st.session_state.profile = "No profile selected"

if "profiles" not in st.session_state:
    st.session_state.profiles = load_profiles()

if "eaters" not in st.session_state:
    st.session_state.eaters = []
    
if "recipes" not in st.session_state:
    st.session_state.recipes = load_recipes()

if "show_add_eater_dialog" not in st.session_state:
    st.session_state.show_add_eater_dialog = False


# ── Constants ───────────────────────────────────────────────────────────────
EMOJI_TO_SEASON = { "☀️": "summer", "❄️": "winter", "🌸": "spring", "🍂": "autumn" }
EMOJI_TO_FOOD_TYPE = { "🥦": "vegan", "🥕": "vegetarian", "🐟": "pescatarian", "🍗": "meat" }
SEASON_TO_EMOJI = {v: k for k, v in EMOJI_TO_SEASON.items()}
FOOD_TYPE_TO_EMOJI = {v: k for k, v in EMOJI_TO_FOOD_TYPE.items()}
COLS_PER_ROW = 5

# ── Header ────────────────────────────────────────────────────────────────────
header_col1, header_col2 = st.columns([5, 1], vertical_alignment="center")

with header_col1:
    st.title("🍽️ Recipe Book")
    st.caption("Simple, seasonal dishes for every table")

with header_col2, st.container(border=True):
    st.selectbox("Change profile", ["No profile selected"] + list(st.session_state.profiles.keys()), key="profile", on_change=lambda: st.session_state.update({"profile": st.session_state.profile}))

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
seasons = list(EMOJI_TO_SEASON.keys())
food_types = list(EMOJI_TO_FOOD_TYPE.keys())
col1, col2, col3 , col4= st.columns([1, 1, 1, 5])
with col1:
    season_filter = st.segmented_control("🌿 Season", ["All"] + seasons, default="All")
with col2:
    food_type_filter = st.segmented_control("🍲 Food type", ["All"] + food_types, default="All")
with col3:
    sort_by = st.selectbox("↕️ Sort by", ["Title", "Score ↓", "Servings"])
with col4, st.container(border=True):
    eater_col1, eater_col2 = st.columns([10, 1], vertical_alignment="center")
    with eater_col1:
        st.write("**People eating**")
    with eater_col2:
        if st.button("Add eater", use_container_width=True):
            st.session_state.show_add_eater_dialog = True
            st.rerun()
    if st.session_state.show_add_eater_dialog:
        add_eater_dialog()


    # Eater cards
    EATERS_PER_ROW = 5

    for i in range(0, len(st.session_state.eaters), EATERS_PER_ROW):
        row = st.session_state.eaters[i:i + EATERS_PER_ROW]
        cols = st.columns(EATERS_PER_ROW, gap="small")

        for j, (col, eater) in enumerate(zip(cols, row)):
            eater_index = i + j

            with col, st.container(border=True):
                    eater_col1, eater_col2 = st.columns([4, 1], vertical_alignment="center")

                    with eater_col1:
                        st.write(f"👤 {eater}")

                    with eater_col2:
                        st.button(
                            "✕",
                            key=f"remove_eater_{eater_index}",
                            on_click=lambda idx=eater_index: st.session_state.eaters.pop(idx),
                        )

filtered = st.session_state.recipes if season_filter == "All" else [r for r in st.session_state.recipes if r["season"] == EMOJI_TO_SEASON.get(season_filter, "")]

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

        with col, st.container(border=True):
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