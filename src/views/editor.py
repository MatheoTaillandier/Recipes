import pandas as pd
import streamlit as st

from recipe_book import importer, storage, ui
from recipe_book.models import COURSES, DIETS, MEALS, PRICES, SEASONS, UNITS, empty_recipe, normalize

recipe_id = st.query_params.get("id", "")
draft = st.session_state.get("editor_draft")

if recipe_id:
    original = storage.get_recipe(recipe_id)
    if original is None:
        st.warning("Cette recette est introuvable. Elle a peut-être été supprimée.", icon="🤷")
        st.page_link(ui.HOME, label="Retour à toutes les recettes", icon="⬅️")
        st.stop()
    load_key = f"edit:{recipe_id}"
elif draft:
    original, load_key = draft, f"draft:{id(draft)}"
else:
    original, load_key = empty_recipe(), "new"


def load_form(recipe: dict) -> None:
    """Copy a recipe into the form widgets."""
    st.session_state.update({
        "ed_title": recipe["title"],
        "ed_description": recipe["description"],
        "ed_servings": recipe["servings"],
        "ed_courses": recipe["courses"],
        "ed_meals": recipe["meals"],
        "ed_seasons": recipe["seasons"],
        "ed_diet": recipe["diet"],
        "ed_prep": recipe["prep_time"],
        "ed_cook": recipe["cook_time"],
        "ed_price": recipe["price"],
        "ed_cost": recipe["cost"],
        "ed_steps": "\n".join(recipe["steps"]),
        "ed_notes": recipe["notes"],
    })
    rows = recipe["ingredients"] or [{"quantity": None, "unit": "", "name": ""}]
    table = pd.DataFrame(rows, columns=["quantity", "unit", "name"])
    table["unit"] = table["unit"].where(table["unit"] != "", None)  # empty cells instead of a blank option
    st.session_state.ed_ingredients = table
    st.session_state.ed_version = st.session_state.get("ed_version", 0) + 1  # resets the table widget
    st.session_state.ed_loaded = load_key


if st.session_state.get("ed_loaded") != load_key:
    load_form(original)

is_new = not recipe_id
st.title("➕ Nouvelle recette" if is_new else f"✏️ Modifier « {original['title']} »")
if draft and is_new:
    st.success("La recette a été lue depuis votre fichier. Vérifiez les informations ci-dessous, puis cliquez "
               "sur **Enregistrer la recette**.", icon="📥")
elif is_new:
    with st.container(horizontal=True, vertical_alignment="center"):
        st.caption("Remplissez ce que vous savez — seuls le nom et une photo sont obligatoires. "
                   "Vous pourrez la modifier à tout moment.")
        st.page_link(ui.IMPORT, label="Vous avez un fichier de recette ? Importez-le", icon="📥")

# ── General information ─────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Général")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.text_input("Nom de la recette *", key="ed_title", placeholder="ex. La tarte aux pommes de mamie")
        st.text_area("Courte description", key="ed_description", height=90,
                     placeholder="Qu'est-ce qui rend ce plat spécial ?")
    with right:
        current_image = storage.image_path(original) if not draft else None
        draft_image = importer.decode_image_data(original.get("image_data", "")) if draft else None
        has_photo = bool(current_image or draft_image)
        upload = st.file_uploader("Remplacer la photo" if has_photo else "Photo *", type=storage.IMAGE_TYPES,
                                  key=f"ed_photo_{load_key}",
                                  help="Une photo du plat terminé, affichée sur la fiche recette. Obligatoire.")
        if upload is not None:
            st.image(upload, width=220)
        elif has_photo:
            st.image(str(current_image) if current_image else draft_image[1], width=220)

with st.container(border=True):
    st.subheader("Détails")
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.number_input("👥 Pour combien de personnes ? *", min_value=1, max_value=100, step=1,
                        key="ed_servings",
                        help="Les quantités saisies ci-dessous sont pour ce nombre de personnes. L'application "
                             "les recalcule automatiquement quand vous cuisinez pour plus ou moins de monde.")
        st.number_input("🔪 Temps de préparation (minutes)", min_value=0, max_value=2000, step=5, key="ed_prep")
        st.number_input("🔥 Temps de cuisson (minutes)", min_value=0, max_value=2000, step=5, key="ed_cook")
    with c2:
        st.pills("Partie du repas *", list(COURSES), format_func=COURSES.get, selection_mode="multi",
                 key="ed_courses", help="Choisissez-en autant que vous voulez — une soupe peut être une entrée et "
                                        "un plat.")
        st.pills("Repas", list(MEALS), format_func=MEALS.get, selection_mode="multi", key="ed_meals",
                 help="Quand mangeriez-vous ce plat ? Choisissez-en autant que vous voulez.")
        st.pills("Saison", list(SEASONS), format_func=SEASONS.get, selection_mode="multi", key="ed_seasons",
                 help="Laissez vide si cette recette se fait toute l'année.")
    with c3:
        st.segmented_control("Prix", list(PRICES), format_func=PRICES.get, key="ed_price")
        st.number_input("💶 Coût estimé en € (facultatif)", min_value=0.0, max_value=10000.0, step=0.5,
                        key="ed_cost", format="%.2f",
                        help="Coût total pour le nombre de personnes ci-dessus. Il est adapté comme les "
                             "ingrédients.")
        st.pills("Régime", list(DIETS), format_func=DIETS.get, key="ed_diet")

# ── Ingredients ─────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🧂 Ingrédients")
    st.caption(f"Quantités pour **{st.session_state.ed_servings}** "
               f"personne{'s' if st.session_state.ed_servings != 1 else ''}. Cliquez sur une case pour écrire, "
               "utilisez le **+** sous le tableau pour ajouter une ligne, sélectionnez une ligne et appuyez sur "
               "la corbeille pour la retirer. Laissez la quantité vide pour « sel, selon le goût ».")
    units = list(dict.fromkeys([u for u in UNITS if u] + [u for u in st.session_state.ed_ingredients["unit"] if isinstance(u, str) and u]))
    ingredients = st.data_editor(
        st.session_state.ed_ingredients,
        key=f"ed_table_{st.session_state.ed_version}",
        num_rows="dynamic",
        hide_index=True,
        placeholder="",
        width="stretch",
        column_order=["quantity", "unit", "name"],
        column_config={
            "quantity": st.column_config.NumberColumn("Quantité", min_value=0, step=0.01, format="%g",
                                                      width="small"),
            "unit": st.column_config.SelectboxColumn("Unité", options=units, width="small",
                                                     format_func=lambda u: UNITS.get(u, u),
                                                     help="Laissez vide pour ce qui se compte tel quel (2 œufs)."),
            "name": st.column_config.TextColumn("Ingrédient", width="large"),
        },
    )
    with st.expander("✍️ Coller plutôt une liste d'ingrédients"):
        pasted = st.text_area("Un ingrédient par ligne, ex. « 200 g de farine » ou « 2 œufs »", key="ed_paste",
                              height=150)
        if st.button("Ajouter ces ingrédients au tableau", disabled=not pasted.strip()):
            parsed = [importer.parse_ingredient_line(line) for line in pasted.splitlines() if line.strip()]
            current = ingredients.dropna(subset=["name"])
            current = current[current["name"].astype(str).str.strip() != ""]
            added = pd.DataFrame(parsed)
            added["unit"] = added["unit"].where(added["unit"] != "", None)
            st.session_state.ed_ingredients = pd.concat([current, added], ignore_index=True)
            st.session_state.ed_version += 1
            del st.session_state["ed_paste"]
            st.rerun()

# ── Instructions ────────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("👩‍🍳 Préparation")
    st.text_area("Écrivez une étape par ligne — elles seront numérotées automatiquement.", key="ed_steps",
                 height=220,
                 placeholder="Préchauffer le four à 180 °C.\nMélanger la farine et le sucre.\nEnfourner 30 minutes.")
    st.text_area("📝 Notes (facultatif)", key="ed_notes", height=90,
                 placeholder="Astuces, variantes, accord mets-vin…")


# ── Save ────────────────────────────────────────────────────────────────────
def collect() -> dict:
    rows = []
    for row in ingredients.to_dict("records"):
        name = str(row.get("name") or "").strip()
        if name and name.lower() != "nan":
            unit = row.get("unit")
            rows.append({"quantity": row.get("quantity"), "unit": unit if isinstance(unit, str) else "",
                         "name": name})
    recipe = dict(original)
    recipe.update({
        "id": recipe_id,
        "title": st.session_state.ed_title.strip(),
        "description": st.session_state.ed_description,
        "servings": st.session_state.ed_servings,
        "courses": st.session_state.ed_courses,
        "meals": st.session_state.ed_meals,
        "seasons": st.session_state.ed_seasons,
        "diet": st.session_state.ed_diet,
        "prep_time": st.session_state.ed_prep,
        "cook_time": st.session_state.ed_cook,
        "price": st.session_state.ed_price,
        "cost": st.session_state.ed_cost,
        "ingredients": rows,
        "steps": st.session_state.ed_steps.splitlines(),
        "notes": st.session_state.ed_notes,
    })
    return normalize(recipe)


with st.container(horizontal=True, horizontal_alignment="right", key="editor_actions"):
    cancel = st.button("Annuler", icon="✖️")
    save = st.button("Enregistrer la recette", icon="💾", type="primary")

if cancel:
    st.session_state.pop("editor_draft", None)
    if recipe_id:
        st.switch_page(ui.RECIPE, query_params={"id": recipe_id})
    st.switch_page(ui.HOME)

if save:
    recipe = collect()
    if not recipe["title"]:
        st.error("Merci de donner un nom à votre recette (en haut de la page).", icon="✋")
        st.stop()
    if not st.session_state.ed_courses:
        st.error("Merci de choisir au moins une partie du repas (entrée, plat ou dessert).", icon="✋")
        st.stop()
    mine = storage.find_duplicate(recipe, storage.load_recipes()) if draft and is_new else None
    if mine:
        st.error(f"Vous avez déjà une recette nommée **{mine['title']}**. Donnez un autre nom à celle-ci, "
                 "ou annulez pour garder votre version.", icon="♻️")
        st.stop()
    if upload is None and not has_photo:
        st.error("Merci d'ajouter une photo du plat (en haut de la page).", icon="📷")
        st.stop()
    image_data = original.get("image_data") if draft else None
    recipe.pop("image_data", None)
    if draft:
        recipe["image"] = None  # an imported recipe never points to someone else's photo file
    saved = storage.save_recipe(recipe)
    if upload is not None:
        storage.remove_image(saved)
        saved["image"] = storage.store_image(saved["id"], upload.name, upload.getvalue())
    elif image_data:
        decoded = importer.decode_image_data(image_data)
        if decoded:
            saved["image"] = storage.store_image(saved["id"], *decoded)
    storage.save_recipe(saved)
    st.session_state.pop("editor_draft", None)
    st.session_state.pop("ed_loaded", None)
    ui.flash(f"« {saved['title']} » a été enregistrée")
    st.switch_page(ui.RECIPE, query_params={"id": saved["id"]})
