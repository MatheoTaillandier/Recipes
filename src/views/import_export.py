import streamlit as st

from recipe_book import importer, storage, ui
from recipe_book.models import COURSES

st.title("📥 Importer et exporter")

# ── Import ──────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Importer une recette depuis un fichier")
    st.markdown(
        "Fichiers acceptés :\n"
        "- **Fichiers de recette de cette application** (`.json`) — ex. une recette envoyée par un ami, "
        "ou une sauvegarde\n"
        "- **Pages web** (`.html`) — ouvrez une recette sur un site de cuisine, utilisez "
        "*Fichier › Enregistrer la page sous…*, puis importez le fichier enregistré\n"
        "- **Fichiers texte** (`.txt`, `.md`) — la première ligne est le nom, suivie d'une partie "
        "*Ingrédients* et d'une partie *Préparation*"
    )
    with st.expander("Voir un exemple de fichier texte"):
        st.code("Crêpes\nDes crêpes moelleuses pour un dimanche tranquille.\nPour : 4\n"
                "Temps de préparation : 10 min\nTemps de cuisson : 20 min\n\nIngrédients\n- 250 g de farine\n"
                "- 2 œufs\n- 50 cl de lait\n- 1 pincée de sel\n\nPréparation\n1. Mélanger la farine et les œufs.\n"
                "2. Verser le lait petit à petit en fouettant.\n"
                "3. Cuire à la louche dans une poêle chaude et beurrée, 1 minute par face.", language=None)

    upload = st.file_uploader("Choisir un fichier de recette", type=["json", "html", "htm", "txt", "md"],
                              key="import_file")
    if upload is not None:
        try:
            found = importer.parse_recipe_file(upload.name, upload.getvalue())
        except ValueError as error:
            found = []
            st.error(str(error), icon="⚠️")
        else:
            if not found:
                st.error("Aucune recette n'a été trouvée dans ce fichier. Vérifiez qu'il est dans l'un des "
                         "formats acceptés ci-dessus.", icon="⚠️")

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
            st.success(f"Trouvé : **{recipe['title']}** · {len(recipe['ingredients'])} ingrédients · "
                       f"{len(recipe['steps'])} étapes", icon="✅")
            if mine:
                st.warning(f"Vous avez déjà une recette nommée **{mine['title']}**, elle ne sera donc pas "
                           "ajoutée une deuxième fois.", icon="♻️")
                with st.container(horizontal=True):
                    st.page_link(ui.RECIPE, label="Ouvrir ma version", icon="👀", query_params={"id": mine["id"]})
                    if st.button("Remplacer la mienne par celle-ci", icon="🔁"):
                        saved = storage.save_imported(recipe, replace=mine)
                        ui.flash(f"« {saved['title']} » a été mise à jour depuis le fichier", "🔁")
                        st.switch_page(ui.RECIPE, query_params={"id": saved["id"]})
            elif st.button("Vérifier et enregistrer cette recette", icon="👉", type="primary"):
                st.session_state.editor_draft = recipe
                st.session_state.pop("ed_loaded", None)
                st.switch_page(ui.EDITOR)
        elif len(found) > 1:
            st.success(f"**{len(found)} recettes** trouvées dans ce fichier.", icon="✅")
            for recipe in found:
                status = (" · *déjà dans votre carnet*" if storage.duplicate_key(recipe) in duplicates
                          else " · 🆕 nouvelle")
                st.markdown(f"- **{recipe['title']}** — {', '.join(COURSES[c] for c in recipe['courses'])}{status}")
            replace = False
            if duplicates:
                choice = st.radio(
                    f"{len(duplicates)} de ces recettes sont déjà dans votre carnet. Que faut-il en faire ?",
                    ["Les ignorer (garder mes versions)", "Remplacer mes versions par celles du fichier"],
                    key="import_duplicates")
                replace = choice.startswith("Remplacer")
            to_import = [r for r in found if replace or storage.duplicate_key(r) not in duplicates]
            if not to_import:
                st.info("Toutes ces recettes sont déjà dans votre carnet — il n'y a rien de nouveau à importer.",
                        icon="👍")
            elif st.button(f"Importer {len(to_import)} recette{'s' if len(to_import) != 1 else ''}", icon="📥",
                           type="primary"):
                for recipe in to_import:
                    storage.save_imported(recipe, replace=duplicates.get(storage.duplicate_key(recipe)))
                ui.flash(f"{len(to_import)} recette{'s importées' if len(to_import) != 1 else ' importée'}", "📥")
                st.switch_page(ui.HOME)

# ── Export ──────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Sauvegarder toutes mes recettes")
    recipes = storage.load_recipes()
    st.write(f"Téléchargez vos **{len(recipes)} recettes** (avec leurs photos) dans un seul fichier. "
             "Gardez-le en lieu sûr, ou importez-le sur un autre ordinateur.")
    st.download_button("Télécharger la sauvegarde", data=importer.export_recipes(recipes, storage.image_path),
                       file_name="sauvegarde-carnet-de-recettes.json", mime="application/json", icon="💾",
                       on_click="ignore", disabled=not recipes, type="primary")
    st.caption(f"Vos recettes sont enregistrées sur cet ordinateur, dans le dossier `{storage.DATA_DIR}`.")
