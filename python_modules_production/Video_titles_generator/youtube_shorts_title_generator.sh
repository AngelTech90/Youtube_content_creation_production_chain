#!/bin/bash

# ==========================================
# script_runner.sh
# Generic Python module launcher
# ------------------------------------------
# - Activates venv (assumes it exists)
# - Installs requirements.txt
# - Runs main Python script
# - Deactivates when done
# ==========================================

set -e  # Stop on error

REQUIREMENTS_FILE="requirements.txt"

# --- Detect main Python script ---
# Look for any .py file in current directory (not in venv, bin, lib, etc.)
PYTHON_SCRIPT=$(find . -maxdepth 1 -name "*.py" -type f | head -n 1)

if [ -z "$PYTHON_SCRIPT" ]; then
    echo "❌ No Python script found in $(pwd)"
    exit 1
fi

# Remove leading ./
PYTHON_SCRIPT="${PYTHON_SCRIPT#./}"

echo "🎯 Target script: $PYTHON_SCRIPT"

# --- Activate venv ---
echo "🚀 Activating virtual environment..."
source "bin/activate"

# --- Run the Python script ---
echo "▶️ Running Python script: $PYTHON_SCRIPT"
python3 "$PYTHON_SCRIPT" 

# --- Deactivate environment ---
echo "🧹 Deactivating virtual environment..."
deactivate
