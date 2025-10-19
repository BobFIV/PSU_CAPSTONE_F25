#!/bin/bash
# Master setup script — automates AE creation + Django update
# Run this instead of running each script manually

SCRIPT_DIR="$(dirname "$0")"

# Step 1: Create AE
bash "$SCRIPT_DIR/create_ae.sh"

# Step 2: Update Django views automatically
echo ""
read -p "Add this AE to Django views.py? (y/n): " REPLY
if [[ "$REPLY" == "y" || "$REPLY" == "Y" ]]; then
    bash "$SCRIPT_DIR/update_views.sh"
fi

# Step 3 (optional): Append values
echo ""
read -p "Would you like to append more values now? (y/n): " REPLY2
if [[ "$REPLY2" == "y" || "$REPLY2" == "Y" ]]; then
    bash "$SCRIPT_DIR/append_ae_values.sh"
fi

echo ""
echo "✅ AE setup and Django update complete!"
