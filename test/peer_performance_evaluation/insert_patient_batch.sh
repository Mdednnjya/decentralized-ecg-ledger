#!/bin/bash

SERVER="http://10.34.100.125:3000"

for i in {101..105}; do
  PID="GROUP06_PAT$i"
  echo "🚀 Uploading ECG data for $PID"

  curl -s -H "X-User-Role: admin" -X POST $SERVER/ecg/upload \
    -H "Content-Type: application/json" \
    -d "{
      \"patientId\": \"$PID\",
      \"ecgData\": {
        \"patientInfo\": {\"id\": \"$PID\", \"age\": 30, \"gender\": \"M\", \"symptoms\": \"chest pain\"},
        \"recordInfo\": {\"deviceId\": \"ECG-001\", \"timestamp\": \"2025-06-10T10:00:00Z\", \"samplingRate\": 500},
        \"leads\": {\"I\": [0.1, 0.2, 0.3], \"II\": [0.2, 0.3, 0.4]},
        \"analysis\": {\"heartRate\": 80, \"rhythm\": \"normal\"}
      },
      \"metadata\": {\"hospital\": \"Hospital Name\", \"doctor\": \"Dr. Name\", \"department\": \"Cardiology\"}
    }" | jq .

  echo "⏳ Waiting for verification to complete..."
  for attempt in {1..10}; do
    STATUS=$(curl -s -H "X-User-Role: doctor" -X GET $SERVER/ecg/access/$PID | jq -r .status)
    echo "🔍 Attempt $attempt: Status = $STATUS"
    if [ "$STATUS" == "CONFIRMED" ]; then
      echo "✅ Verification confirmed!"
      break
    fi
    sleep 3
  done

  echo "✅ Granting access for $PID"
  curl -s -H "X-User-Role: patient" -X POST $SERVER/ecg/grant-access \
    -H "Content-Type: application/json" \
    -d "{\"patientId\": \"$PID\"}" | jq .

  echo "📥 Accessing data for $PID (doctor)"
  curl -s -H "X-User-Role: doctor" -X GET $SERVER/ecg/access/$PID | jq .

  echo "🔒 Revoking access for $PID"
  curl -s -H "X-User-Role: patient" -X POST $SERVER/ecg/revoke-access \
    -H "Content-Type: application/json" \
    -d "{\"patientId\": \"$PID\"}" | jq .

  echo "🚫 Accessing after revoke for $PID"
  curl -s -H "X-User-Role: doctor" -X GET $SERVER/ecg/access/$PID | jq .

  echo "📜 Checking audit trail for $PID"
  curl -s -H "X-User-Role: patient" -X GET $SERVER/ecg/audit/$PID | jq .

  echo "----------------------"
  sleep 4  # jeda antar pasien biar tidak nabrak
done

echo "✅ All patients inserted and tested."
