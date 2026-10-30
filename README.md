# 🍽️ My Recipe Book

A personal recipe book that runs in your web browser, on your own computer.
Your recipes are saved locally and are **never published online**.

## Start it

| Computer | What to do |
| --- | --- |
| **Windows** | Double-click `start.bat` |
| **Mac** | Double-click `start.command` (the first time: right-click › *Open*, then confirm) |
| **Linux** | Run `./start.command` |

The first launch takes a minute (it installs what it needs). The recipe book then opens in your
browser at <http://localhost:8501>. Keep the black window open while you cook; close it to stop.

Developers can also run `uv run main.py`.

## What you can do

- **Browse** all recipes as cards, search by name *or ingredient*, and filter by course
  (starter / main / dessert), meal, season, diet, price and total time.
- **People eating** — change the number at the top and every ingredient amount and cost is
  recalculated (on the cards and on each recipe page). The number is remembered for next time.
- **Add a recipe** with the orange button. Enter the name, a photo, how many people the recipe is
  for, preparation & cooking time, price, meal, part of the meal, season, ingredients and steps.
  Ingredients can be typed into the table or pasted as a list (“200 g flour”, “2 eggs”…).
- **Edit** or **delete** any recipe from its page, and give it a star rating.
- **Import** a recipe from a file (*Import / Export* in the menu):
  - a `.json` recipe file from this app (e.g. sent by a friend) or a full backup,
  - a web page saved from a cooking website (`.html`, *File › Save page as…*),
  - a plain text / Markdown file (`.txt`, `.md`) with *Ingredients* and *Instructions* sections.
- **Download** a single recipe as a **PDF** (to print, with amounts for the number of people eating)
  or as a recipe file to share it, or **back up** your whole book (photos included).

## Where are my recipes?

In the `my_recipes/` folder next to this file — one `.json` file per recipe, plus an `images/`
folder. This folder is ignored by git so it is never pushed to GitHub. Copy it (or use
*Import / Export › Download backup*) to keep a backup.

On the very first launch, three example recipes are added so the book isn't empty; delete them
whenever you like.
