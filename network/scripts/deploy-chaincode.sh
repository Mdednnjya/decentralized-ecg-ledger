#!/bin/bash

set -e

echo "=== Starting chaincode deployment process ==="

# VM IP Addresses
VM2_IP="10.34.100.126"  # Peer0.Org1
VM3_IP="10.34.100.128"  # Peer1.Org1  
VM4_IP="10.34.100.114"  # Peer0.Org2
VM5_IP="10.34.100.116"  # Peer1.Org2

# Set environment variables
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel
export CC_NAME=ecgcc
export CC_SRC_PATH=../chaincode/ecg_chaincode
export CC_VERSION=1.0
export CC_SEQUENCE=1

# Package chaincode if not exists
if [ ! -f "${CC_NAME}.tar.gz" ]; then
    echo "Packaging chaincode..."
    peer lifecycle chaincode package ${CC_NAME}.tar.gz \
        --path ${CC_SRC_PATH} \
        --lang node \
        --label ${CC_NAME}_${CC_VERSION}
else
    echo "Chaincode package already exists, skipping packaging..."
fi

# Helper function to install chaincode with check
install_chaincode() {
    local peer_name=$1
    local peer_ip=$2
    local peer_port=$3
    
    export CORE_PEER_ADDRESS=$peer_ip:$peer_port
    
    echo "Checking if chaincode installed on $peer_name ($peer_ip:$peer_port)..."
    
    if peer lifecycle chaincode queryinstalled | grep -q "${CC_NAME}_${CC_VERSION}"; then
        echo "✓ Chaincode already installed on $peer_name, skipping..."
    else
        echo "Installing chaincode on $peer_name..."
        peer lifecycle chaincode install ${CC_NAME}.tar.gz
        echo "✓ Chaincode installed on $peer_name"
    fi
}

# Organization 1 - Install
echo "=== Organization 1 - Installation ==="
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

install_chaincode "peer0.org1" $VM2_IP 7051
install_chaincode "peer1.org1" $VM3_IP 8051

# Get package ID
export CORE_PEER_ADDRESS=$VM2_IP:7051
PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_${CC_VERSION} | awk '{print $3}' | cut -d ',' -f1)
echo "Package ID: $PACKAGE_ID"

# Check if Org1 already approved
echo "Checking Org1 approval status..."
if peer lifecycle chaincode checkcommitreadiness \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --output json | grep -q '"Org1MSP": true'; then
    echo "✓ Org1 already approved, skipping..."
else
    echo "Approving chaincode for Org1..."
    peer lifecycle chaincode approveformyorg -o 10.34.100.121:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --channelID ${CHANNEL_NAME} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id ${PACKAGE_ID} \
        --sequence ${CC_SEQUENCE} \
        --init-required \
        --tls \
        --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
    echo "✓ Org1 approved"
fi

# Organization 2 - Install
echo "=== Organization 2 - Installation ==="
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp

install_chaincode "peer0.org2" $VM4_IP 9051
install_chaincode "peer1.org2" $VM5_IP 10051

# Check if Org2 already approved
echo "Checking Org2 approval status..."
export CORE_PEER_ADDRESS=$VM4_IP:9051
if peer lifecycle chaincode checkcommitreadiness \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --output json | grep -q '"Org2MSP": true'; then
    echo "✓ Org2 already approved, skipping..."
else
    echo "Approving chaincode for Org2..."
    peer lifecycle chaincode approveformyorg -o 10.34.100.121:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --channelID ${CHANNEL_NAME} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id ${PACKAGE_ID} \
        --sequence ${CC_SEQUENCE} \
        --init-required \
        --tls \
        --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
    echo "✓ Org2 approved"
fi

# Check commit readiness
echo "Checking commit readiness..."
peer lifecycle chaincode checkcommitreadiness \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --output json

# Check if already committed
if peer lifecycle chaincode querycommitted --channelID ${CHANNEL_NAME} | grep -q "${CC_NAME}"; then
    echo "✓ Chaincode already committed, skipping commit and init..."
else
    echo "Committing chaincode to channel..."
    peer lifecycle chaincode commit -o 10.34.100.121:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --channelID ${CHANNEL_NAME} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --sequence ${CC_SEQUENCE} \
        --init-required \
        --tls \
        --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
        --peerAddresses $VM2_IP:7051 \
        --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
        --peerAddresses $VM4_IP:9051 \
        --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

    echo "Initializing chaincode..."
    peer chaincode invoke -o 10.34.100.121:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --tls \
        --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
        -C ${CHANNEL_NAME} \
        -n ${CC_NAME} \
        --isInit \
        -c '{"function":"initLedger","Args":[]}' \
        --peerAddresses $VM2_IP:7051 \
        --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
        --peerAddresses $VM4_IP:9051 \
        --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
    
    echo "✓ Chaincode initialized"
fi

echo "✓ Chaincode deployment completed successfully!"

# Verify deployment
echo "Verifying chaincode deployment..."
peer lifecycle chaincode querycommitted --channelID ${CHANNEL_NAME}
