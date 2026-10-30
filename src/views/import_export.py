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

        # The same recipe listed twice in one file is only imported once.
        unique = {}
        for recipe in found:
            unique.setdefault(storage.duplicate_key(recipe), recipe)
        found = list(unique.values())
        existing = storage.load_recipes()
        duplicates = {storage.duplicate_key(r): storage.find_duplicate(r, existing) for r in found}
        duplicates = {k: v for k, v in duplicates.items() if v}

        if len(found) == 1:
            recipe = found[0]
            mine = duplicates.get(storage.duplicate_key(recipe))
            st.success(f"Found **{recipe['title']}** · {len(recipe['ingredients'])} ingredients · "
                       f"{len(recipe['steps'])} steps", icon="✅")
            if mine:
                st.warning(f"You already have a recipe called **{mine['title']}**, so it won't be added "
                           "a second time.", icon="♻️")
                with st.container(horizontal=True):
                    st.page_link(ui.RECIPE, label="Open my version", icon="👀", query_params={"id": mine["id"]})
                    if st.button("Replace mine with this one", icon="🔁"):
                        saved = storage.save_imported(recipe, replace=mine)
                        ui.flash(f"“{saved['title']}” was updated from the file", "🔁")
                        st.switch_page(ui.RECIPE, query_params={"id": saved["id"]})
            elif st.button("Review and save this recipe", icon="👉", type="primary"):
                st.session_state.editor_draft = recipe
                st.session_state.pop("ed_loaded", None)
                st.switch_page(ui.EDITOR)
        elif len(found) > 1:
            st.success(f"Found **{len(found)} recipes** in this file.", icon="✅")
            for recipe in found:
                status = " · *already in your book*" if storage.duplicate_key(recipe) in duplicates else " · 🆕 new"
                st.markdown(f"- **{recipe['title']}** — {', '.join(COURSES[c] for c in recipe['courses'])}{status}")
            replace = False
            if duplicates:
                choice = st.radio(
                    f"{len(duplicates)} of these recipes are already in your book. What should happen to them?",
                    ["Skip them (keep my versions)", "Replace my versions with the ones from the file"],
                    key="import_duplicates")
                replace = choice.startswith("Replace")
            to_import = [r for r in found if replace or storage.duplicate_key(r) not in duplicates]
            if not to_import:
                st.info("All these recipes are already in your book — there is nothing new to import.", icon="👍")
            elif st.button(f"Import {len(to_import)} recipe{'s' if len(to_import) != 1 else ''}", icon="📥",
                           type="primary"):
                for recipe in to_import:
                    storage.save_imported(recipe, replace=duplicates.get(storage.duplicate_key(recipe)))
                ui.flash(f"{len(to_import)} recipe{'s were' if len(to_import) != 1 else ' was'} imported", "📥")
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
