#!/bin/bash
# ==========================================
# distribute_runner.sh
# Copies run_python_module.sh into every
# subdirectory of the parent directory
# ==========================================

set -e

SCRIPT_NAME="script_runner.sh"

# Ensure the file exists
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "❌ $SCRIPT_NAME not found in current directory!"
    exit 1
fi

# Get parent directory
PARENT_DIR="./python_modules_production"

echo "📂 Distributing $SCRIPT_NAME to all directories under:"
echo "   $PARENT_DIR"
echo

# Copy into each subdirectory
find "$PARENT_DIR" -type d -mindepth 1 -maxdepth 1 | while read -r dir; do
    echo "➡️  Copying into: $dir"
    cp "$SCRIPT_NAME" "$dir/"
done

echo
echo "✅ Distribution complete!"

