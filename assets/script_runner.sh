#!/bin/bash
# ==========================================
# run_python_module.sh
# Generic Python module launcher
# ------------------------------------------
# - Activates or creates venv
# - Installs requirements
# - Runs main Python script
# - Deactivates when done
# ==========================================

set -e  # stop on error

VENV_DIR="./venv"
REQUIREMENTS_FILE="requirements.txt"

# --- Detect main Python script ---
# If only one .py file exists, use it
# Else prefer one named main.py or the same as folder
MODULE_NAME=$(basename "$PWD")
PYTHON_SCRIPT=$(ls *.py 2>/dev/null | grep -E "^(main|${MODULE_NAME})\.py$" || ls *.py 2>/dev/null | head -n 1)

if [ -z "$PYTHON_SCRIPT" ]; then
    echo "❌ No Python script found in $(pwd)"
    exit 1
fi

echo "🎯 Target script: $PYTHON_SCRIPT"

# --- Create virtual environment if missing ---
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️ Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# --- Activate venv ---
echo "🚀 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# --- Upgrade pip ---
python -m pip install --upgrade pip

# --- Install dependencies ---
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "📦 Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "⚠️ No requirements.txt found. Skipping dependency installation."
fi

# --- Run the Python script ---
echo "▶️ Running Python script: $PYTHON_SCRIPT"
python "$PYTHON_SCRIPT"

# --- Deactivate environment ---
echo "🧹 Deactivating virtual environment..."
deactivate

echo "✅ Done. Environment cleaned up."

