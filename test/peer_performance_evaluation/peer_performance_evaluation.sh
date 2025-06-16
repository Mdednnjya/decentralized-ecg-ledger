#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

run_insert_batch() {
    read -p "🩺 Ingin melakukan transaksi baru (upload + akses 5 pasien)? (yes/no): " choice
    if [[ "$choice" == "yes" ]]; then
        echo "⏳ Menjalankan insert_patient_batch.sh untuk 5 pasien..."
        sleep 1
        ./insert_patient_batch.sh
        echo "✅ Transaksi pasien selesai dijalankan."
    else
        echo "❎ Melewati transaksi pasien baru."
    fi
}

run_fetch_logs() {
    echo ""
    echo "🚀 [1/3] Menjalankan fetch_peer_logs.sh..."
    ./fetch_peer_logs.sh

    PENGUJIAN_DIR=$(ls -dt pengujian_* | head -n 1)
    echo "📁 Direktori hasil fetch terbaru: $PENGUJIAN_DIR"

    if [ ! -d "$PENGUJIAN_DIR/logs" ]; then
        echo "❌ Folder logs tidak ditemukan di $PENGUJIAN_DIR"
        exit 1
    fi
}

run_analyze() {
    echo ""
    echo "🔍 [2/3] Menjalankan analyze_logs.py..."
    python3 analyze_logs.py

    if [ ! -d "$PENGUJIAN_DIR/output" ]; then
        echo "❌ Folder output tidak ditemukan setelah analisa"
        exit 1
    fi
}

run_view() {
    echo ""
    echo "📊 [3/3] Menampilkan semua CSV dari: $PENGUJIAN_DIR/output/"
    for file in "$PENGUJIAN_DIR"/output/*.csv; do
        echo ""
        echo "================= FILE: $file ================="
        python3 view_csv.py "$file"
        echo ""
    done
}

# ==== MAIN ====
main() {
    run_insert_batch
    run_fetch_logs
    run_analyze
    run_view
    echo ""
    echo "✅ Semua proses selesai!"
}

main
