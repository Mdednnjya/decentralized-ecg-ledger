#!/bin/bash
set -euo pipefail

# --- Konfigurasi ---
IPFS_CONTAINER="${IPFS_CONTAINER:-ipfs.example.com}"
RESULT_FILE="ipfs_performance_results.txt"
OP_TIMEOUT=60         # Timeout tiap operasi (detik)
# --------------------

rm -f "$RESULT_FILE"

log(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a "$RESULT_FILE"; }

log "Mulai Uji Performa IPFS"
log "Container: $IPFS_CONTAINER"
log "Hasil akan disimpan di: $RESULT_FILE"
echo "=========================================" >> "$RESULT_FILE"

test_file_size(){
  SIZE_KB=$1
  DESC="$2"
  TMP_HOST="/tmp/testfile_${SIZE_KB}kb.bin"
  TMP_CONT="/tmp/testfile_${SIZE_KB}kb.bin"

  log ""
  log "=== Menguji: $DESC (${SIZE_KB} KB) ==="

    # 1) Buat & copy file
  log "1) Membuat dummy di host"
  head -c "${SIZE_KB}K" /dev/urandom > "$TMP_HOST"
  log "2) Copy ke container"
  docker cp "$TMP_HOST" "${IPFS_CONTAINER}:${TMP_CONT}"

  # 2) Upload & ukur dengan time -p
  log "3) Upload (ipfs add)"
  UP_OUT=$(docker exec "$IPFS_CONTAINER" timeout $OP_TIMEOUT sh -c \
    "{ time -p ipfs add -q $TMP_CONT; } 2>&1")
  # baris pertama = HASH; cari line "real XX.XX"
  HASH=$(printf '%s\n' "$UP_OUT" | head -n1)
  REAL_UP=$(printf '%s\n' "$UP_OUT" | sed -n 's/^real //p')
  log "   → Upload Hash: $HASH"
  log "   → Waktu Upload: ${REAL_UP}s"

  # 3) Download & ukur dengan time -p
  log "4) Download (ipfs cat)"
  DL_OUT=$(docker exec "$IPFS_CONTAINER" timeout $OP_TIMEOUT sh -c \
    "{ time -p ipfs cat $HASH > /dev/null; } 2>&1")
  REAL_DL=$(printf '%s\n' "$DL_OUT" | sed -n 's/^real //p')
  log "   → Waktu Download: ${REAL_DL}s"

  # 4) Cleanup
  log "5) Cleanup"
  docker exec "$IPFS_CONTAINER" rm -f "$TMP_CONT" || true
    rm -f "$TMP_HOST"

  log "=== Selesai: $DESC ==="
}

# Jalankan test
test_file_size 10    "10 KB (kecil)"
test_file_size 1024  "1 MB (sedang)"
test_file_size 5120  "5 MB (besar)"

log ""
log "=== UJI PERFORMA IPFS SELESAI ==="