#!/bin/bash

# --- KonfigurASI ---
TARGET_URL="${TARGET_URL:-http://10.34.100.125:3000}"
RESULT_FILE="api_performance_results.txt"
TRANSACTION_COUNT=20    # Jumlah transaksi untuk uji throughput
VALIDATION_WAIT=12      # Delay validasi peer (detik) sebelum grant-access atau antar-upload di E2E
# --------------------

# Bersihkan file hasil lama
rm -f "$RESULT_FILE"

echo "Memulai Uji Performa API Klien..."             | tee -a "$RESULT_FILE"
echo "Hasil akan disimpan di: ${RESULT_FILE}"       | tee -a "$RESULT_FILE"
echo "========================================="     | tee -a "$RESULT_FILE"
echo "WAKTU: $(date '+%Y-%m-%d %H:%M:%S')"            | tee -a "$RESULT_FILE"
echo "========================================="     | tee -a "$RESULT_FILE"
echo ""                                              | tee -a "$RESULT_FILE"

# Fungsi ukur latency
measure_request() {
    DESC="$1"; EP="$2"; DATA="$3"; ROLE="$4"
    echo "--- Latency: ${DESC} ---"                   | tee -a "$RESULT_FILE"
    START=$(date +%s.%N)

    if [ -z "$DATA" ]; then
        CODE=$(curl -s -o /dev/null -w '%{http_code}' "$TARGET_URL$EP")
    else
        CODE=$(curl -s -o /dev/null -w '%{http_code}' \
            -X POST "$TARGET_URL$EP" \
            -H 'Content-Type: application/json' \
            -H "X-User-Role: $ROLE" \
            -d "$DATA")
    fi

    END=$(date +%s.%N)
    LAT=$(echo "$END - $START" | bc)
    echo "HTTP_CODE: $CODE"                          | tee -a "$RESULT_FILE"
    echo "LATENCY   : ${LAT}s"                       | tee -a "$RESULT_FILE"
    echo ""                                          | tee -a "$RESULT_FILE"
}

# --- Bagian Latency ---
measure_request "Health Check" "/health" "" ""
measure_request "Upload Data" "/ecg/upload" \
  '{"patientId":"LAT-TEST","ecgData":{"info":"small"},"metadata":{}}' \
  "admin"

# Tunggu validasi sebelum grant-access
echo "⏳ Menunggu ${VALIDATION_WAIT}s validasi blockchain sebelum grant-access..." | tee -a "$RESULT_FILE"
sleep "$VALIDATION_WAIT"
echo "✅ Validasi selesai, lanjut grant-access"      | tee -a "$RESULT_FILE"
echo ""                                              | tee -a "$RESULT_FILE"

measure_request "Grant Access" "/ecg/grant-access" \
  '{"patientId":"LAT-TEST"}' \
  "patient"

# --- Throughput Murni (RAW) ---
echo "=== Throughput Murni: $TRANSACTION_COUNT Upload (tanpa delay) ===" | tee -a "$RESULT_FILE"
START_RAW=$(date +%s.%N)
for i in $(seq 1 $TRANSACTION_COUNT); do
    pid="RAW-${i}"
    curl -s -o /dev/null -X POST "$TARGET_URL/ecg/upload" \
         -H 'Content-Type: application/json' \
         -H 'X-User-Role: admin' \
         -d "{\"patientId\":\"${pid}\",\"ecgData\":{\"seq\":${i}},\"metadata\":{}}"
done
END_RAW=$(date +%s.%N)
DUR_RAW=$(echo "$END_RAW - $START_RAW" | bc)
TPS_RAW=$(echo "scale=2; $TRANSACTION_COUNT / $DUR_RAW" | bc)
echo "Total waktu raw    : ${DUR_RAW}s"               | tee -a "$RESULT_FILE"
echo "TPS (raw)          : ${TPS_RAW} req/s"          | tee -a "$RESULT_FILE"
echo ""                                               | tee -a "$RESULT_FILE"

# --- Throughput End-to-End (E2E) ---
echo "=== Throughput E2E: $TRANSACTION_COUNT Upload (dengan ${VALIDATION_WAIT}s delay) ===" | tee -a "$RESULT_FILE"
START_E2E=$(date +%s.%N)
for i in $(seq 1 $TRANSACTION_COUNT); do
    pid="E2E-${i}"
    echo "[$i/$TRANSACTION_COUNT] Upload ${pid} ..."  | tee -a "$RESULT_FILE"
    curl -s -o /dev/null -X POST "$TARGET_URL/ecg/upload" \
         -H 'Content-Type: application/json' \
         -H 'X-User-Role: admin' \
         -d "{\"patientId\":\"${pid}\",\"ecgData\":{\"seq\":${i}},\"metadata\":{}}"
    echo " → Menunggu ${VALIDATION_WAIT}s validasi"    | tee -a "$RESULT_FILE"
    sleep "$VALIDATION_WAIT"
done
END_E2E=$(date +%s.%N)
DUR_E2E=$(echo "$END_E2E - $START_E2E" | bc)
TPS_E2E=$(echo "scale=2; $TRANSACTION_COUNT / $DUR_E2E" | bc)
echo "Total waktu E2E    : ${DUR_E2E}s"               | tee -a "$RESULT_FILE"
echo "TPS (E2E)          : ${TPS_E2E} req/s"          | tee -a "$RESULT_FILE"
echo ""                                               | tee -a "$RESULT_FILE"

echo "=== UJI PERFORMA SELESAI ==="                    | tee -a "$RESULT_FILE"
echo "Lihat detail di ${RESULT_FILE}"                 | tee -a "$RESULT_FILE"
