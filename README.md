# 🍽️ Mon carnet de recettes

Un carnet de recettes personnel qui fonctionne dans votre navigateur, sur votre propre ordinateur.
Vos recettes sont enregistrées sur votre ordinateur et ne sont **jamais publiées en ligne**.

## Le lancer

| Ordinateur | Que faire |
| --- | --- |
| **Windows** | Double-cliquez sur `start.bat` |
| **Mac** | Double-cliquez sur `start.command` (la première fois : clic droit › *Ouvrir*, puis confirmez) |
| **Linux** | Lancez `./start.command` |

Le premier lancement prend une minute (il installe ce dont il a besoin). Le carnet de recettes s'ouvre
ensuite dans votre navigateur à l'adresse <http://localhost:8501>. Gardez la fenêtre noire ouverte pendant que
vous cuisinez ; fermez-la pour quitter.

Les développeurs peuvent aussi lancer `uv run main.py`.

## Ce que vous pouvez faire

- **Parcourir** toutes les recettes sous forme de fiches, chercher par nom *ou par ingrédient*, et filtrer par
  partie du repas (entrée / plat / dessert), repas, saison, régime, prix et temps total.
- **Nombre de convives** — changez le nombre en haut de la page et les quantités et le coût de chaque
  ingrédient sont recalculés (sur les fiches et sur chaque page de recette). Le nombre est gardé pour la
  prochaine fois.
- **Ajouter une recette** avec le bouton orange. Indiquez le nom, une photo (obligatoire), pour combien de
  personnes est la recette, les temps de préparation et de cuisson, le prix, le repas, la partie du repas, la
  saison, les ingrédients et les étapes. Les ingrédients peuvent être saisis dans le tableau ou collés sous
  forme de liste (« 200 g de farine », « 2 œufs »…).
- **Modifier** ou **supprimer** n'importe quelle recette depuis sa page, et lui donner une note en étoiles.
- **Importer** une recette depuis un fichier (*Importer / Exporter* dans le menu) :
  - un fichier de recette `.json` de cette application (ex. envoyé par un ami) ou une sauvegarde complète,
  - une page web enregistrée depuis un site de cuisine (`.html`, *Fichier › Enregistrer la page sous…*),
  - un fichier texte / Markdown (`.txt`, `.md`) avec une partie *Ingrédients* et une partie *Préparation*.

  Les recettes que vous avez déjà (même nom, sans tenir compte des majuscules ni des accents) ne sont jamais
  ajoutées deux fois : vous choisissez de garder votre version ou de la remplacer par celle du fichier.
- **Télécharger** une recette en **PDF** (à imprimer, avec les quantités pour le nombre de convives) ou en
  fichier de recette pour la partager, ou **sauvegarder** tout votre carnet (photos comprises).

## Où sont mes recettes ?

Dans le dossier `my_recipes/` à côté de ce fichier — un fichier `.json` par recette, plus un dossier `images/`.
Ce dossier est ignoré par git, il n'est donc jamais envoyé sur GitHub. Copiez-le (ou utilisez
*Importer / Exporter › Télécharger la sauvegarde*) pour garder une sauvegarde.

Au tout premier lancement, trois recettes d'exemple sont ajoutées pour que le carnet ne soit pas vide ;
supprimez-les quand vous voulez.
