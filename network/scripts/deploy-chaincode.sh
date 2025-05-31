#!/bin/bash

set -e

echo "Starting chaincode deployment process..."

# Set environment variables
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel
export CC_NAME=ecgcc
export CC_SRC_PATH=../chaincode/ecg_chaincode
export CC_VERSION=1.0
export CC_SEQUENCE=1
export CC_INIT_FCN=initLedger
export CC_END_POLICY="AND('Org1MSP.peer','Org2MSP.peer')"
export PACKAGE_ID=""

echo "Chaincode details:"
echo "- Name: $CC_NAME"
echo "- Version: $CC_VERSION"
echo "- Source: $CC_SRC_PATH"
echo "- Channel: $CHANNEL_NAME"

# Check if chaincode source exists
if [ ! -d "$CC_SRC_PATH" ]; then
    echo "Error: Chaincode source directory $CC_SRC_PATH does not exist!"
    exit 1
fi

# Package chaincode
echo "Packaging chaincode..."
peer lifecycle chaincode package ${CC_NAME}.tar.gz \
    --path ${CC_SRC_PATH} \
    --lang node \
    --label ${CC_NAME}_${CC_VERSION}

echo "Chaincode packaged successfully!"

# Organization 1 - Install and Approve
echo "=== Organization 1 - Installation and Approval ==="
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051

# Install chaincode on peer0.org1
echo "Installing chaincode on peer0.org1..."
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Install chaincode on peer1.org1
echo "Installing chaincode on peer1.org1..."
export CORE_PEER_ADDRESS=peer1.org1.example.com:8051
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Get package ID
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
echo "Querying installed chaincodes..."
peer lifecycle chaincode queryinstalled

PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_${CC_VERSION} | awk '{print $3}' | cut -d ',' -f1)

if [ -z "$PACKAGE_ID" ]; then
    echo "Error: Could not get package ID!"
    exit 1
fi

echo "Package ID: $PACKAGE_ID"

# Approve chaincode for Org1
echo "Approving chaincode for Org1..."
peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "Org1 approval completed!"

# Organization 2 - Install and Approve
echo "=== Organization 2 - Installation and Approval ==="
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=peer0.org2.example.com:9051

# Install chaincode on peer0.org2
echo "Installing chaincode on peer0.org2..."
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Install chaincode on peer1.org2
echo "Installing chaincode on peer1.org2..."
export CORE_PEER_ADDRESS=peer1.org2.example.com:10051
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Approve chaincode for Org2
echo "Approving chaincode for Org2..."
export CORE_PEER_ADDRESS=peer0.org2.example.com:9051
peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "Org2 approval completed!"

# Check commit readiness
echo "Checking commit readiness..."
peer lifecycle chaincode checkcommitreadiness \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --output json

# Commit chaincode
echo "Committing chaincode to channel..."
peer lifecycle chaincode commit -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    --peerAddresses peer0.org1.example.com:7051 \
    --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses peer0.org2.example.com:9051 \
    --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

echo "Chaincode committed successfully!"

# Initialize chaincode
echo "Initializing chaincode..."
peer chaincode invoke -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    -C ${CHANNEL_NAME} \
    -n ${CC_NAME} \
    --isInit \
    -c '{"function":"initLedger","Args":[]}' \
    --peerAddresses peer0.org1.example.com:7051 \
    --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses peer0.org2.example.com:9051 \
    --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

echo "Chaincode initialized successfully!"

# Query committed chaincodes for verification
echo "Verifying chaincode deployment..."
peer lifecycle chaincode querycommitted --channelID ${CHANNEL_NAME}

echo "Chaincode deployment completed successfully!"
echo "Chaincode $CC_NAME version $CC_VERSION is now ready for use on channel $CHANNEL_NAME"
