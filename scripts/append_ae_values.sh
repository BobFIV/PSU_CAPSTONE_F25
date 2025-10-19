#!/bin/bash
# ==========================================
# OneM2M AE Value Append Script (ACME-CSE)
# Author: Eiman
#
# Description:
#   Appends new data values to existing AE containers.
#
# Usage:
#   chmod +x append_values.sh
#   ./append_values.sh
# ==========================================

BASE_URL="http://54.164.106.20:8080/cse-in"
RVI="3"

echo "-------------------------------------------"
echo "oneM2M AE Value Append Script"
echo "-------------------------------------------"

read -p "Enter existing AE name (e.g., Device_1): " AE_NAME
read -p "Enter Originator (e.g., CAdmin or CDevice1): " ORIGIN

CONTAINERS=("temperature" "humidity" "battery" "signal")

echo ""
echo "Enter new values for each container in AE '$AE_NAME':"
declare -A NEW_VALUES
for CNT in "${CONTAINERS[@]}"; do
  read -p "  $CNT: " VALUE
  NEW_VALUES["$CNT"]=$VALUE
done
echo ""

# Step 2: Append Data
for CNT in "${CONTAINERS[@]}"; do
  VALUE=${NEW_VALUES[$CNT]}
  echo "Posting new value '$VALUE' to container $CNT ..."
  curl -s -i -X POST "$BASE_URL/$AE_NAME/$CNT" \
    -H "X-M2M-Origin: $ORIGIN" \
    -H "X-M2M-RVI: $RVI" \
    -H "X-M2M-RI: req_${AE_NAME}_${CNT}_append" \
    -H "Content-Type: application/json;ty=4" \
    -d "{
          \"m2m:cin\": {
            \"con\": \"$VALUE\"
          }
        }"
  echo ""
done

echo "All new values appended successfully."
echo "-------------------------------------------"
echo "You can verify the updates using:"
echo "curl -X GET $BASE_URL/$AE_NAME \\"
echo "     -H \"X-M2M-Origin: $ORIGIN\" \\"
echo "     -H \"X-M2M-RVI: $RVI\""
echo "-------------------------------------------"
