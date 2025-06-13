#!/bin/bash
# Menyimpan argumen ke variabel agar mudah dibaca
ORDERER_TS="$1"
PEER_TS="$2"
# Mengonversi timestamp ke format angka (nanodetik)
ORDERER_NANOS=$(date -d "${ORDERER_TS}" +"%s%N")
PEER_NANOS=$(date -d "${PEER_TS}" +"%s%N")
# Menghitung selisih
DIFFERENCE_NANOS=$((PEER_NANOS - ORDERER_NANOS))
# Mengonversi kembali ke milidetik agar mudah dibaca
DIFFERENCE_MS=$(echo "scale=3; ${DIFFERENCE_NANOS} / 1000000" | bc)
# Mencetak hasil
echo "Waktu Propagasi Blok: ${DIFFERENCE_MS} ms"
