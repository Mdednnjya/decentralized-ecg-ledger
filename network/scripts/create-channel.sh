#!/bin/bash

# Set environment variables
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel

# Organization 1
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=10.34.1.1:7051

# Create channel
peer channel create -o 10.34.1.10:7050 -c $CHANNEL_NAME \
    --ordererTLSHostnameOverride orderer.example.com \
    -f ./channel-artifacts/${CHANNEL_NAME}.tx \
    --outputBlock ./channel-artifacts/${CHANNEL_NAME}.block \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Join peer0.org1.example.com to the channel
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Update anchor peers for Org1
peer channel update -o 10.34.1.10:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    -c $CHANNEL_NAME \
    -f ./channel-artifacts/Org1MSPanchors.tx \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Join peer1.org1 to the channel
export CORE_PEER_ADDRESS=10.34.1.2:8051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Organization 2
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=10.34.1.3:9051

# Join peer0.org2.example.com to the channel
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Update anchor peers for Org2
peer channel update -o 10.34.1.10:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    -c $CHANNEL_NAME \
    -f ./channel-artifacts/Org2MSPanchors.tx \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Join peer1.org2 to the channel
export CORE_PEER_ADDRESS=10.34.1.4:10051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

echo "Channel created and peers joined successfully"