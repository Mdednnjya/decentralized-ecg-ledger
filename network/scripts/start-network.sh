#!/bin/bash

# Start Certificate Authorities
docker-compose -f docker-compose-ca.yaml up -d

# Start the orderer
docker-compose -f docker-compose-orderer.yaml up -d

# Start the peers
# Note: In a real distributed deployment, these would be started on different machines
docker-compose -f docker-compose-peer-org1-peer0.yaml up -d
docker-compose -f docker-compose-peer-org1-peer1.yaml up -d
docker-compose -f docker-compose-peer-org2-peer0.yaml up -d
docker-compose -f docker-compose-peer-org2-peer1.yaml up -d

# Start the client with IPFS
docker-compose -f docker-compose-client.yaml up -d

echo "Network started successfully"