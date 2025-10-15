#!/bin/bash

# URL of the CSE where the AE will be registered
CSE_URL="http://54.164.106.20:8080/cse-in"

# AE details
RN="TestDevice"             # Resource Name for AE
API="N.org.demo.device"     # Application ID for AE
AEI="TestDevice1"           # AE Instance ID (unique identifier)
PI="/cse-in"                # Parent ID (CSE root path)

# Request ID (unique identifier for the request)
X_M2M_RI="tempReq2"

# Admin origin
X_M2M_ORIGIN="CAdmin"

# Version identifier
X_M2M_RVI="3"

# Send POST request to register the AE
curl -i -X POST "$CSE_URL" \
  -H "X-M2M-Origin: $X_M2M_ORIGIN" \
  -H "X-M2M-RVI: $X_M2M_RVI" \
  -H "X-M2M-RI: $X_M2M_RI" \
  -H "Content-Type: application/json" \
  -d '{
        "m2m:ae": {
            "rn": "'"$RN"'",              
            "api": "'"$API"'",    
            "aei": "'"$AEI"'",           
            "pi": "'"$PI"'"
    }'
