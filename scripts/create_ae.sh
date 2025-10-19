#!/bin/bash
# ==========================================
# OneM2M AE Creation Script (ACME-CSE)
# Author: Eiman
#
# Description:
#   Interactive script to create a new AE with containers
#   and user-defined initial values.
#
# Usage:
#   chmod +x create_ae.sh
#   ./create_ae.sh
# ==========================================

BASE_URL="http://54.164.106.20:8080/cse-in"
RVI="3"

echo "-------------------------------------------"
echo "oneM2M AE Creation Script"
echo "-------------------------------------------"

read -p "Enter AE name (e.g., Device_1): " AE_NAME
read -p "Enter Originator (e.g., CAdmin or CDevice1): " ORIGIN

AE_API="N.org.demo.${AE_NAME,,}"

echo ""
echo "Configuration Summary:"
echo "-------------------------------------------"
echo "Base URL:   $BASE_URL"
echo "AE Name:    $AE_NAME"
echo "Originator: $ORIGIN"
echo "API ID:     $AE_API"
echo "-------------------------------------------"
sleep 1

# Step 1: Create AE
echo "Creating AE: $AE_NAME ..."
curl -s -i -X POST "$BASE_URL" \
  -H "X-M2M-Origin: $ORIGIN" \
  -H "X-M2M-RVI: $RVI" \
  -H "X-M2M-RI: req_${AE_NAME}_create" \
  -H "Content-Type: application/json;ty=2" \
  -d "{
        \"m2m:ae\": {
          \"rn\": \"$AE_NAME\",
          \"api\": \"$AE_API\",
          \"rr\": true,
          \"srv\": [\"3\"]
        }
      }"
echo ""
echo "AE '$AE_NAME' creation request sent."
echo ""

# Step 2: Create Containers
CONTAINERS=("temperature" "humidity" "battery" "signal")

for CNT in "${CONTAINERS[@]}"; do
  echo "Creating container: $CNT ..."
  curl -s -i -X POST "$BASE_URL/$AE_NAME" \
    -H "X-M2M-Origin: $ORIGIN" \
    -H "X-M2M-RVI: $RVI" \
    -H "X-M2M-RI: req_${AE_NAME}_${CNT}" \
    -H "Content-Type: application/json;ty=3" \
    -d "{
          \"m2m:cnt\": {
            \"rn\": \"$CNT\",
            \"mni\": 100
          }
        }"
  echo ""
done
echo "All containers created."
echo ""

# Step 3: Input User Data Values
declare -A INPUT_VALUES

echo "Enter initial values for each container:"
for CNT in "${CONTAINERS[@]}"; do
  read -p "  $CNT: " VALUE
  INPUT_VALUES["$CNT"]=$VALUE
done
echo ""

# Step 4: Add User Data to Containers
for CNT in "${CONTAINERS[@]}"; do
  VALUE=${INPUT_VALUES[$CNT]}
  echo "Posting value '$VALUE' to container $CNT ..."
  curl -s -i -X POST "$BASE_URL/$AE_NAME/$CNT" \
    -H "X-M2M-Origin: $ORIGIN" \
    -H "X-M2M-RVI: $RVI" \
    -H "X-M2M-RI: req_${AE_NAME}_${CNT}_data" \
    -H "Content-Type: application/json;ty=4" \
    -d "{
          \"m2m:cin\": {
            \"con\": \"$VALUE\"
          }
        }"
  echo ""
done

echo "All user-defined data values posted."
echo ""
echo "-------------------------------------------"
echo "AE '$AE_NAME' setup complete."
echo "Verify AE using:"
echo "curl -X GET $BASE_URL/$AE_NAME \\"
echo "     -H \"X-M2M-Origin: $ORIGIN\" \\"
echo "     -H \"X-M2M-RVI: $RVI\""
echo "-------------------------------------------"
