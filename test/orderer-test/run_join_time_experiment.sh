#!/bin/bash

# --- Konfigurasi (sesuaikan jika perlu) ---
CHANNEL_NAME="ecg-jointime-test"
RESULT_FILE="join_time_experiment.txt"
BASE_PATH=${PWD}
export FABRIC_CFG_PATH=${BASE_PATH}
export CORE_PEER_TLS_ENABLED=true
# ------------------------------------

echo "Memulai pengukuran waktu join..."

# Skenario 1: Join peer pertama (0 peer lain aktif)
echo "" >> $RESULT_FILE
echo "--- Skenario 1 (0 Peer Lain Aktif) - Join peer0.org1 ---" >> $RESULT_FILE

export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH=${BASE_PATH}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=${BASE_PATH}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_ADDRESS=10.34.100.126:7051 # Target peer0.org1

(time peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block) >> $RESULT_FILE 2>&1
echo "peer0.org1 selesai join."
sleep 2

# Skenario 2: Join peer kedua (1 peer lain aktif)
echo "" >> $RESULT_FILE
echo "--- Skenario 2 (1 Peer Lain Aktif) - Join peer0.org2 ---" >> $RESULT_FILE

export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_MSPCONFIGPATH=${BASE_PATH}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=${BASE_PATH}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_ADDRESS=10.34.100.114:9051 # Target peer0.org2

(time peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block) >> $RESULT_FILE 2>&1
echo "peer0.org2 selesai join."
sleep 2

# Skenario 3: Join peer ketiga (2 peer lain aktif)
echo "" >> $RESULT_FILE
echo "--- Skenario 3 (2 Peer Lain Aktif) - Join peer1.org1 ---" >> $RESULT_FILE

export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH=${BASE_PATH}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=${BASE_PATH}/crypto-config/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
export CORE_PEER_ADDRESS=10.34.100.128:8051 # Target peer1.org1

(time peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block) >> $RESULT_FILE 2>&1
echo "peer1.org1 selesai join."
sleep 2

# Skenario 4: Join peer keempat (3 peer lain aktif)
echo "" >> $RESULT_FILE
echo "--- Skenario 4 (3 Peer Lain Aktif) - Join peer1.org2 ---" >> $RESULT_FILE

export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_MSPCONFIGPATH=${BASE_PATH}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_TLS_ROOTCERT_FILE=${BASE_PATH}/crypto-config/peerOrganizations/org2.example.com/peers/peer1.org2.example.com/tls/ca.crt
export CORE_PEER_ADDRESS=10.34.100.116:10051 # Target peer1.org2

(time peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block) >> $RESULT_FILE 2>&1
echo "peer1.org2 selesai join."

echo ""
echo "=== EKSPERIMEN SELESAI ==="
echo "Silakan cek file '${RESULT_FILE}' untuk melihat hasilnya."
cat $RESULT_FILE
