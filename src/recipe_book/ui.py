"""Shared look & feel: styling, header navigation and session state helpers."""

from __future__ import annotations

import streamlit as st

from . import storage

CSS = """
<style>
.block-container { padding-top: 3.5rem; max-width: 1200px; }
h1, h2, h3 { letter-spacing: -0.01em; }
.rb-brand { font-family: Georgia, "Times New Roman", serif; font-size: 2rem; font-weight: 700;
  line-height: 1.15; color: #2f2620; }
.rb-tagline { color: #7a6a5c; margin-top: 0.2rem; font-size: 0.95rem; }
.rb-placeholder {
  height: 170px; border-radius: 0.6rem; display: flex; align-items: center; justify-content: center;
  font-size: 4rem; background: linear-gradient(135deg, #fbe3cf, #f6efe6);
}
.rb-card-title { font-size: 1.15rem; font-weight: 650; margin: 0.4rem 0 0.1rem 0; line-height: 1.3; }
.rb-card-desc { color: #6d5f53; font-size: 0.9rem; min-height: 2.6em; margin-bottom: 0.4rem;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.rb-meta { color: #6d5f53; font-size: 0.85rem; display: flex; flex-wrap: wrap; gap: 0.35rem 0.9rem; margin: 0.2rem 0 0.6rem 0; }
.rb-chip { display: inline-block; background: #f6e7da; color: #8a4b22; border-radius: 999px;
  padding: 0.1rem 0.6rem; font-size: 0.78rem; margin: 0 0.25rem 0.25rem 0; }
.rb-hero-img img { border-radius: 0.8rem; object-fit: cover; }
[data-testid="stImage"] img { border-radius: 0.6rem; object-fit: cover; aspect-ratio: 4 / 3; }
.rb-step { display: flex; gap: 0.8rem; margin-bottom: 0.9rem; }
.rb-step-num { flex: none; width: 1.8rem; height: 1.8rem; border-radius: 50%; background: #c8642b; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; }
.rb-step-text { padding-top: 0.15rem; line-height: 1.55; }
.rb-empty { text-align: center; padding: 3rem 1rem; color: #7a6a5c; }
.rb-empty div { font-size: 3.5rem; }
@media print {
  header, [data-testid="stToolbar"], .rb-noprint, button { display: none !important; }
}
</style>
"""


def init_state() -> None:
    if "people" not in st.session_state:
        st.session_state.people = int(storage.load_settings().get("people", 2))


def set_people(value: int) -> None:
    """Remember how many people are eating (kept between visits)."""
    value = max(1, int(value))
    st.session_state.people = value
    settings = storage.load_settings()
    if settings.get("people") != value:
        settings["people"] = value
        storage.save_settings(settings)


def people_input(key: str, label: str = "👥 People eating") -> int:
    """Number input bound to the shared 'people eating' value."""
    st.session_state[key] = st.session_state.people

    def on_change():
        set_people(st.session_state[key])

    return int(st.number_input(label, min_value=1, max_value=100, step=1, key=key, on_change=on_change,
                               help="Ingredient amounts and cost are recalculated for this number of people."))


def flash(message: str, icon: str = "✅") -> None:
    """Queue a toast that survives a page switch."""
    st.session_state["_flash"] = (message, icon)


def show_flash() -> None:
    if "_flash" in st.session_state:
        message, icon = st.session_state.pop("_flash")
        st.toast(message, icon=icon)


HOME, RECIPE, EDITOR, IMPORT = "views/home.py", "views/recipe.py", "views/editor.py", "views/import_export.py"


def header() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    left, right = st.columns([1, 1], vertical_alignment="center")
    with left:
        st.markdown('<div class="rb-brand">🍽️ My Recipe Book</div>'
                    '<div class="rb-tagline">Your family recipes, kept safely on this computer</div>',
                    unsafe_allow_html=True)
    with right, st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center",
                                     key="rb_nav"):
        st.page_link(HOME, label="All recipes", icon="📖")
        st.page_link(IMPORT, label="Import / Export", icon="📥")
        if st.button("Add a recipe", icon="➕", type="primary", key="nav_add"):
            st.session_state.pop("editor_draft", None)
            st.session_state.pop("ed_loaded", None)
            st.switch_page(EDITOR)
    st.divider()
