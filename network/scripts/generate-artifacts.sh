#!/bin/bash

# Generate crypto material using cryptogen
cryptogen generate --config=./crypto-config.yaml

# Generate the genesis block and channel transaction
configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block
configtxgen -profile TwoOrgsChannel -outputCreateChannelTx ./channel-artifacts/ecgchannel.tx -channelID ecgchannel

# Generate anchor peer updates for Org1 and Org2
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org1MSPanchors.tx -channelID ecgchannel -asOrg Org1MSP
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org2MSPanchors.tx -channelID ecgchannel -asOrg Org2MSP