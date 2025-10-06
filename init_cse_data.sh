#!/bin/bash
# -------------------------------------------------------------
# Initialize oneM2M ACME CSE with DummyData containers and values
# -------------------------------------------------------------

CSE_URL="http://54.164.106.20:8080/cse-in/DummyData"
HEADERS=(-H "X-M2M-Origin: CAdmin" -H "X-M2M-RVI: 3" -H "Accept: application/json")

echo "-------------------------------------------"
echo "Initializing DummyData AE on oneM2M CSE"
echo "-------------------------------------------"

# Helper function
create_container() {
  local name=$1
  echo "Creating container: $name ..."
  curl -s -o /dev/null -w "%{http_code}" -X POST "$CSE_URL" \
    -H "X-M2M-Origin: CAdmin" \
    -H "X-M2M-RI: create_${name}" \
    -H "X-M2M-RVI: 3" \
    -H "Content-Type: application/json;ty=3" \
    -d "{\"m2m:cnt\": {\"rn\": \"${name}\"}}" | grep -q "20" && \
    echo "Container '$name' created (or already exists)" || \
    echo "Failed to create container '$name'"
}

add_value() {
  local name=$1
  local value=$2
  echo "   ↳ Adding value $value to $name ..."
  curl -s -o /dev/null -w "%{http_code}" -X POST "$CSE_URL/$name" \
    -H "X-M2M-Origin: CAdmin" \
    -H "X-M2M-RI: add_${name}" \
    -H "X-M2M-RVI: 3" \
    -H "Content-Type: application/json;ty=4" \
    -d "{\"m2m:cin\": {\"con\": \"${value}\"}}" | grep -q "20" && \
    echo "Added value successfully" || \
    echo "Failed to add value"
}

# --- CREATE CONTAINERS ---
create_container temperature
create_container humidity
create_container battery
create_container signal

# --- ADD SAMPLE VALUES ---
add_value temperature 25.4
add_value humidity 56
add_value battery 88
add_value signal 4

echo "-------------------------------------------"
echo "Done! You can verify via:"
echo "curl ${CSE_URL}/temperature/la -H 'X-M2M-Origin: CAdmin' -H 'X-M2M-RVI: 3' -H 'Accept: application/json'"
echo "-------------------------------------------"
