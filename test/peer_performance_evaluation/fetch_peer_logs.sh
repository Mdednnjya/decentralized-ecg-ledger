#!/bin/bash

# Buat nama direktori berbasis timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ROOT_DIR="pengujian_$TIMESTAMP"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

# Mapping IP ke container
declare -A PEERS
PEERS["10.34.100.126"]="group5@10.34.100.126 peer0.org1.example.com"
PEERS["10.34.100.128"]="group6@10.34.100.128 peer1.org1.example.com"
PEERS["10.34.100.114"]="group1@10.34.100.114 peer0.org2.example.com"
PEERS["10.34.100.116"]="group2@10.34.100.116 peer1.org2.example.com"

echo "📥 Fetching logs to: $LOG_DIR"
for IP in "${!PEERS[@]}"; do
    ENTRY=(${PEERS[$IP]})
    USER_AT_HOST=${ENTRY[0]}
    PEER_CONTAINER=${ENTRY[1]}

    echo "🔄 $PEER_CONTAINER from $USER_AT_HOST..."

    ssh "$USER_AT_HOST" "
        docker logs $PEER_CONTAINER 2>&1 | grep 'Committed block' | tail -n 60| while read -r line; do
            # Extract data pakai sed
            echo \"\$line\" | sed -n 's/.*Committed block \[\([0-9]*\)\] with.* in \([0-9]*\)ms (state_validation=\([0-9]*\)ms block_and_pvtdata_commit=\([0-9]*\)ms state_commit=\([0-9]*\)ms) commitHash=\[\(.*\)\].*/Block=\1 | Time=\2ms (state_validation=\3ms block_and_pvtdata_commit=\4ms state_commit=\5ms) | Hash=\6/p'
        done
    " > "$LOG_DIR/$PEER_CONTAINER.log"
done

echo "✅ Log collection completed at: $LOG_DIR"
