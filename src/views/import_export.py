import streamlit as st

from recipe_book import importer, storage, ui
from recipe_book.models import COURSES

st.title("📥 Import & export")

# ── Import ──────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Import a recipe from a file")
    st.markdown(
        "Supported files:\n"
        "- **Recipe files from this app** (`.json`) — e.g. a recipe a friend sent you, or a backup\n"
        "- **Web pages** (`.html`) — open a recipe on a cooking website, use *File › Save page as…*, "
        "then import the saved file\n"
        "- **Text files** (`.txt`, `.md`) — the first line is the name, followed by an *Ingredients* section "
        "and an *Instructions* section"
    )
    with st.expander("See an example of a text file"):
        st.code("Pancakes\nFluffy pancakes for a lazy Sunday.\nServes: 4\nPrep time: 10 min\n"
                "Cook time: 20 min\n\nIngredients\n- 250 g flour\n- 2 eggs\n- 500 ml milk\n- 1 pinch salt\n\n"
                "Instructions\n1. Mix the flour and the eggs.\n2. Slowly whisk in the milk.\n"
                "3. Cook ladlefuls in a hot buttered pan, 1 minute per side.", language=None)

    upload = st.file_uploader("Choose a recipe file", type=["json", "html", "htm", "txt", "md"],
                              key="import_file")
    if upload is not None:
        try:
            found = importer.parse_recipe_file(upload.name, upload.getvalue())
        except ValueError as error:
            found = []
            st.error(str(error), icon="⚠️")
        else:
            if not found:
                st.error("No recipe could be found in this file. Check that it is one of the supported "
                         "formats above.", icon="⚠️")

        if len(found) == 1:
            recipe = found[0]
            st.success(f"Found **{recipe['title']}** · {len(recipe['ingredients'])} ingredients · "
                       f"{len(recipe['steps'])} steps", icon="✅")
            if st.button("Review and save this recipe", icon="👉", type="primary"):
                st.session_state.editor_draft = recipe
                st.session_state.pop("ed_loaded", None)
                st.switch_page(ui.EDITOR)
        elif len(found) > 1:
            st.success(f"Found **{len(found)} recipes** in this file.", icon="✅")
            for recipe in found:
                st.markdown(f"- **{recipe['title']}** — {COURSES[recipe['course']]}")
            if st.button(f"Import all {len(found)} recipes", icon="📥", type="primary"):
                for recipe in found:
                    image_data = recipe.pop("image_data", None)
                    recipe["image"] = None
                    saved = storage.save_recipe(recipe)
                    decoded = importer.decode_image_data(image_data) if image_data else None
                    if decoded:
                        saved["image"] = storage.store_image(saved["id"], *decoded)
                        storage.save_recipe(saved)
                ui.flash(f"{len(found)} recipes were imported", "📥")
                st.switch_page(ui.HOME)

# ── Export ──────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Back up all my recipes")
    recipes = storage.load_recipes()
    st.write(f"Download your **{len(recipes)} recipes** (with their photos) in a single file. "
             "Keep it somewhere safe, or import it on another computer.")
    st.download_button("Download backup", data=importer.export_recipes(recipes, storage.image_path),
                       file_name="my-recipe-book-backup.json", mime="application/json", icon="💾",
                       on_click="ignore", disabled=not recipes, type="primary")
    st.caption(f"Your recipes are stored on this computer, in the folder `{storage.DATA_DIR}`.")
