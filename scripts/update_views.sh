#!/bin/bash
# ==========================================
# Script: update_views.sh
# Author: Eiman
#
# Description:
#   Adds a new AE entry into the AE_ENDPOINTS
#   dictionary inside ui/views.py automatically.
#
# Usage:
#   chmod +x update_views.sh
#   ./update_views.sh
# ==========================================

VIEWS_PATH="../demoApp/ui/views.py"     # adjust path if needed
BASE_URL="http://54.164.106.20:8080"

echo "-------------------------------------------"
echo "Update Django views.py with new AE endpoint"
echo "-------------------------------------------"

# Ask for AE details
read -p "Enter AE name (e.g., Device_2): " AE_NAME
read -p "Enter Originator ID (e.g., CDevice2): " ORIGIN

AE_ENDPOINT_LINE="    \"$AE_NAME\": f\"{BASE_URL}/${ORIGIN}\","

# Check if AE already exists in AE_ENDPOINTS
if grep -q "\"$AE_NAME\"" "$VIEWS_PATH"; then
    echo "AE '$AE_NAME' already exists in views.py."
    exit 0
fi

# Insert the new AE line before the closing curly brace of AE_ENDPOINTS
awk -v newline="$AE_ENDPOINT_LINE" '
    /AE_ENDPOINTS = {/,/}/ {
        if ($0 ~ /}/ && !done) {
            print newline
            done=1
        }
    }
    {print}
' "$VIEWS_PATH" > temp_views.py && mv temp_views.py "$VIEWS_PATH"

echo ""
echo "✅ Added new AE endpoint to views.py"
echo ""
echo "AE name:     $AE_NAME"
echo "Originator:  $ORIGIN"
echo "Resulting entry:"
echo "$AE_ENDPOINT_LINE"
echo ""
echo "-------------------------------------------"
echo "You can verify by opening:"
echo "$VIEWS_PATH"
echo "-------------------------------------------"
