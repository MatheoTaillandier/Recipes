#!/bin/bash
# Double-click this file (Mac) or run ./start.command (Linux) to open your recipe book.
cd "$(dirname "$0")" || exit 1
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  echo "First launch: installing uv (the tool that runs the recipe book)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
echo "Starting your recipe book… it will open in your browser."
echo "Keep this window open while you use it. Close it to stop."
uv run main.py
