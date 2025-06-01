#!/bin/bash

set -e

echo "=== Creating Channel for Multi-VM Network ==="

# VM IP Addresses  
VM1_IP="10.34.100.121"  # Orderer
VM2_IP="10.34.100.126"  # Peer0.Org1
VM3_IP="10.34.100.128"  # Peer1.Org1
VM4_IP="10.34.100.114"  # Peer0.Org2  
VM5_IP="10.34.100.116"  # Peer1.Org2

# Set environment variables
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel

echo "Testing connectivity to all peers..."
for ip in $VM2_IP $VM3_IP $VM4_IP $VM5_IP; do
    if nc -z $ip 7051 2>/dev/null || nc -z $ip 8051 2>/dev/null || nc -z $ip 9051 2>/dev/null || nc -z $ip 10051 2>/dev/null; then
        echo "✓ Peer at $ip is reachable"
    else
        echo "✗ Peer at $ip is not reachable on expected ports"
        echo "Please ensure peer is running on VM $ip"
    fi
done

echo "Creating channel: $CHANNEL_NAME"

# Organization 1 - peer0
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=$VM2_IP:7051

# Create channel
echo "Creating channel $CHANNEL_NAME..."
peer channel create -o $VM1_IP:7050 -c $CHANNEL_NAME \
    --ordererTLSHostnameOverride orderer.example.com \
    -f ./channel-artifacts/${CHANNEL_NAME}.tx \
    --outputBlock ./channel-artifacts/${CHANNEL_NAME}.block \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "✓ Channel $CHANNEL_NAME created"

# Join all peers
echo "Joining peers to channel..."

# Peer0.Org1 (VM2)
echo "Joining peer0.org1 ($VM2_IP)..."
export CORE_PEER_ADDRESS=$VM2_IP:7051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Peer1.Org1 (VM3)  
echo "Joining peer1.org1 ($VM3_IP)..."
export CORE_PEER_ADDRESS=$VM3_IP:8051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Update anchor peers for Org1
echo "Updating anchor peers for Org1..."
export CORE_PEER_ADDRESS=$VM2_IP:7051
peer channel update -o $VM1_IP:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    -c $CHANNEL_NAME \
    -f ./channel-artifacts/Org1MSPanchors.tx \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Switch to Org2
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp

# Peer0.Org2 (VM4)
echo "Joining peer0.org2 ($VM4_IP)..."
export CORE_PEER_ADDRESS=$VM4_IP:9051  
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Peer1.Org2 (VM5)
echo "Joining peer1.org2 ($VM5_IP)..."
export CORE_PEER_ADDRESS=$VM5_IP:10051
peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block

# Update anchor peers for Org2
echo "Updating anchor peers for Org2..."
export CORE_PEER_ADDRESS=$VM4_IP:9051
peer channel update -o $VM1_IP:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    -c $CHANNEL_NAME \
    -f ./channel-artifacts/Org2MSPanchors.tx \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "✓ All peers joined channel successfully!"

# Verify
echo "Verifying channel membership..."
export CORE_PEER_ADDRESS=$VM2_IP:7051
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
peer channel list

echo "✓ Channel creation and peer joining completed!"
