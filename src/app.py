import streamlit as st

from recipe_book import storage, ui

st.set_page_config(page_title="Mon carnet de recettes", page_icon="🍽️", layout="wide")

storage.ensure_data_dir()
ui.init_state()

pages = [
    st.Page(ui.HOME, title="Toutes les recettes", icon="📖", default=True),
    st.Page(ui.RECIPE, title="Recette", icon="🍲", url_path="recipe"),
    st.Page(ui.EDITOR, title="Ajouter ou modifier une recette", icon="✏️", url_path="edit"),
    st.Page(ui.IMPORT, title="Importer / Exporter", icon="📥", url_path="import"),
]

pg = st.navigation(pages, position="hidden")
if pg.url_path != "edit":
    # Leaving the editor: the form is reloaded from disk next time it opens.
    st.session_state.pop("ed_loaded", None)

ui.header()
ui.show_flash()
pg.run()
