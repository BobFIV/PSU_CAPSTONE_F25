Example command to redirect

curl -X POST \
  http://ec2-54-164-106-20.compute-1.amazonaws.com:8080/cse-in/cbA_id-mn_STASDhTfYS/aeA_GbK295bvQj/cntA_A2HOvKwhI7 \
  -H "X-M2M-Origin: CAdmin" \
  -H "X-M2M-RI: 12345" \
  -H "X-M2M-RVI: 5" \
  -H "Content-Type: application/json;ty=23" \
  -d '{
    "m2m:sub": {
      "rn": "sub_tempCloudApp",
      "nu": ["https://noelia-exuberant-anomalously.ngrok-free.dev/notify"],
      "nct": 1,
      "enc": { "net": [3] }
    }
  }'

{"m2m:sub": 




To test ngrok

curl -X POST https://noelia-exuberant-anomalously.ngrok-free.dev/notify \
-H "Content-Type: application/json" \
-d '{"m2m:sgn":{"nev":{"rep":{"m2m:cin":{"con":"27.5"}}},"net":3}}}'