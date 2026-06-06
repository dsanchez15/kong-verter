#!/bin/bash
# Launch Kong-verter from the repo root.
# Double-click this file in Finder to run.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ ! -f ".venv/bin/python" ]; then
    osascript -e 'display dialog "Virtual environment not found.\n\nPlease run:\npython3 -m venv .venv\npip install -r requirements.txt" buttons {"OK"} default button "OK" with icon stop with title "Kong-verter"'
    exit 1
fi

source .venv/bin/activate
python src/gui.py &
