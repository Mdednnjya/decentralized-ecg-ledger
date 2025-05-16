#!/bin/bash

# Set environment variables
export FABRIC_CFG_PATH=${PWD}/../
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel
export CC_NAME=ecgcc
export CC_SRC_PATH=../../chaincode/ecg_chaincode
export CC_VERSION=1.0
export CC_SEQUENCE=1
export CC_INIT_FCN=initLedger
export CC_END_POLICY="OR('Org1MSP.peer','Org2MSP.peer')"
export CC_COLL_CONFIG=""
export PACKAGE_ID=""

# Package chaincode
peer lifecycle chaincode package ${CC_NAME}.tar.gz \
    --path ${CC_SRC_PATH} \
    --lang node \
    --label ${CC_NAME}_${CC_VERSION}

# Organization 1
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/../crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/../crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=10.34.1.1:7051

# Install chaincode on peer0.org1
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Get package ID
PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_${CC_VERSION} | awk '{print $3}' | cut -d ',' -f1)
echo "Package ID: ${PACKAGE_ID}"

# Approve chaincode for Org1
peer lifecycle chaincode approveformyorg -o 10.34.1.10:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --tls \
    --cafile ${PWD}/../crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Organization 2
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/../crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/../crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=10.34.1.3:9051

# Install chaincode on peer0.org2
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# Approve chaincode for Org2
peer lifecycle chaincode approveformyorg -o 10.34.1.10:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --tls \
    --cafile ${PWD}/../crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Check commit readiness
peer lifecycle chaincode checkcommitreadiness \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --output json

# Commit chaincode
peer lifecycle chaincode commit -o 10.34.1.10:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --tls \
    --cafile ${PWD}/../crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    --peerAddresses 10.34.1.1:7051 \
    --tlsRootCertFiles ${PWD}/../crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses 10.34.1.3:9051 \
    --tlsRootCertFiles ${PWD}/../crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

# Initialize chaincode
peer chaincode invoke -o 10.34.1.10:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls \
    --cafile ${PWD}/../crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    -C ${CHANNEL_NAME} \
    -n ${CC_NAME} \
    --isInit \
    -c '{"function":"initLedger","Args":[]}' \
    --peerAddresses 10.34.1.1:7051 \
    --tlsRootCertFiles ${PWD}/../crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses 10.34.1.3:9051 \
    --tlsRootCertFiles ${PWD}/../crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

echo "Chaincode deployed successfully"