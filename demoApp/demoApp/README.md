Example command to redirect

curl -X POST \
  http://127.0.0.1:8080/cse-in/cbA_id-mn_3Y6gUwVgo5/aeA_Q0RnDcyaeg/cntA_eG8ei0FaHc \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: 12345" \
  -H "X-M2M-RVI: 5" \
  -H "Content-Type: application/json;ty=23" \
  -d '{
    "m2m:sub": {
      "rn": "sub_localdemo",
      "nu": ["http://127.0.0.1:8000/notify"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'




To test ngrok

curl -X POST https://noelia-exuberant-anomalously.ngrok-free.dev/notify \
-H "Content-Type: application/json" \
-d '{"m2m:sgn":{"nev":{"rep":{"m2m:cin":{"con":"27.5"}}},"net":3}}}'