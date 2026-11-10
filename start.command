#!/bin/bash
# Double-cliquez sur ce fichier (Mac) ou lancez ./start.command (Linux) pour ouvrir votre carnet de recettes.
cd "$(dirname "$0")" || exit 1
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "Premier lancement : installation de uv (l'outil qui fait tourner le carnet de recettes)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
echo "Lancement de votre carnet de recettes… il va s'ouvrir dans votre navigateur."
echo "Gardez cette fenêtre ouverte pendant son utilisation. Fermez-la pour quitter."
uv run main.py
