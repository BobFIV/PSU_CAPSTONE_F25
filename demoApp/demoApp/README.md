Example command to redirect

curl -X POST \
  http://127.0.0.1:8080/cse-in/cbA_id-mn_WeFgxO8cud/aeA_DZuWwz6fDs/cntA_MLF7DXA97C \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: 12345" \
  -H "X-M2M-RVI: 5" \
  -H "Content-Type: application/json;ty=23" \
  -d '{
    "m2m:sub": {
      "rn": "sub_localdemo",
      "nu": ["http://127.0.0.1:8000/notify/"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'


docker build -t acme-in .
docker run -d --name acme-in -p 8080:8080 acme-in

To test ngrok

curl -X POST https://noelia-exuberant-anomalously.ngrok-free.dev/notify \
-H "Content-Type: application/json" \
-d '{"m2m:sgn":{"nev":{"rep":{"m2m:cin":{"con":"27.5"}}},"net":3}}}'



