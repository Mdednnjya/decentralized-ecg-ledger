#!/bin/bash

set -e

echo "Generating crypto material..."

# Create channel-artifacts directory if it doesn't exist
mkdir -p channel-artifacts

# Generate crypto material using cryptogen
cryptogen generate --config=./crypto-config.yaml --output="./crypto-config"

echo "Crypto material generated successfully"

echo "Generating genesis block and channel transaction..."

# Set FABRIC_CFG_PATH to current directory
export FABRIC_CFG_PATH=${PWD}

# Generate the genesis block
configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block

# Generate channel configuration transaction
configtxgen -profile TwoOrgsChannel -outputCreateChannelTx ./channel-artifacts/ecgchannel.tx -channelID ecgchannel

# Generate anchor peer updates for Org1
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org1MSPanchors.tx -channelID ecgchannel -asOrg Org1MSP

# Generate anchor peer updates for Org2
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org2MSPanchors.tx -channelID ecgchannel -asOrg Org2MSP

echo "All artifacts generated successfully!"
echo "Generated files:"
echo "- Genesis block: ./channel-artifacts/genesis.block"
echo "- Channel transaction: ./channel-artifacts/ecgchannel.tx"
echo "- Org1 anchor peer: ./channel-artifacts/Org1MSPanchors.tx"
echo "- Org2 anchor peer: ./channel-artifacts/Org2MSPanchors.tx"
