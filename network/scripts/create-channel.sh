#!/bin/bash

set -e

echo "Starting channel creation process..."

# Set environment variables
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel

echo "Creating channel: $CHANNEL_NAME"

# Organization 1 - peer0
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051

# Create channel
echo "Creating channel $CHANNEL_NAME..."
peer channel create -o orderer.example.com:7050 -c $CHANNEL_NAME \
    --ordererTLSHostnameOverride orderer.example.com \
    -f ./channel-artifacts/${CHANNEL_NAME}.tx \
    --outputBlock ./channel-artifacts/${CHANNEL_NAME}.block \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "Channel $CHANNEL_NAME created successfully!"

# Join peer0.org1 to the channel
echo "Joining peer0.org1.example.com to channel..."
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Update anchor peers for Org1
echo "Updating anchor peers for Org1..."
peer channel update -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    -c $CHANNEL_NAME \
    -f ./channel-artifacts/Org1MSPanchors.tx \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Join peer1.org1 to the channel
echo "Joining peer1.org1.example.com to channel..."
export CORE_PEER_ADDRESS=peer1.org1.example.com:8051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Organization 2 - peer0
echo "Switching to Org2..."
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=peer0.org2.example.com:9051

# Join peer0.org2 to the channel
echo "Joining peer0.org2.example.com to channel..."
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Update anchor peers for Org2
echo "Updating anchor peers for Org2..."
peer channel update -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    -c $CHANNEL_NAME \
    -f ./channel-artifacts/Org2MSPanchors.tx \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Join peer1.org2 to the channel
echo "Joining peer1.org2.example.com to channel..."
export CORE_PEER_ADDRESS=peer1.org2.example.com:10051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

echo "All peers have joined channel $CHANNEL_NAME successfully!"

# List channels for verification
echo "Verifying channel membership..."
peer channel list

echo "Channel creation and peer joining completed successfully!"
