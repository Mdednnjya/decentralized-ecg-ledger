# Decentralized ECG Storage System

A blockchain-based solution for secure management of ECG (Electrocardiogram) data using Hyperledger Fabric and IPFS.

## Project Overview

This project implements a decentralized storage system for ECG data with the following features:

- **Data Integrity**: ECG data is stored on IPFS with hashes stored on the blockchain
- **Secure Sharing**: Fine-grained access control for patient data
- **Auditability**: Complete audit trail of all data access
- **Decentralized Storage**: Patient-controlled access to medical records

## Architecture

The system is built using:

- **Hyperledger Fabric**: Enterprise blockchain platform
- **IPFS**: Distributed file storage
- **RAFT Consensus**: For ordering service consensus
- **Certificate Authorities**: For identity management

## Network Topology

- 1 Orderer Node (10.34.1.10)
- 2 Organizations (Org1 and Org2)
  - Org1: peer0.org1 (10.34.1.1), peer1.org1 (10.34.1.2)
  - Org2: peer0.org2 (10.34.1.3), peer1.org2 (10.34.1.4)
- 1 CA for each Org and Orderer
- 1 Client host (10.34.1.5) for Python + IPFS + SDK

## Prerequisites

All VMs should have:

- Ubuntu 20.04 LTS (or compatible Linux distribution)
- Docker and Docker Compose
- Git
- curl, wget, jq

For the client VM, additionally:
- Python 3.8+ and venv
- Node.js v12+ and npm
- IPFS daemon

## Detailed Setup Instructions

### Initial Setup for All VMs

Run these commands on all 6 VMs to install the basic prerequisites:

```bash
# Update package lists
sudo apt update

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to the docker group
sudo usermod -aG docker $USER

# Install other utilities
sudo apt install -y git curl wget jq
```
Log out and log back in to apply the docker group membership.


### 1. Initial Setup for All VMs
```bash
git clone https://github.com/mdednnjya/decentralized-ecg-ledger.git
cd decentralized-ecg-ledger
```
### 2. Install Hyperledger Fabric Binaries (All VMs)
```bash
# Navigate to project directory
cd ~/decentralized-ecg-ledger

# Download Fabric binaries
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.9 1.5.5 -d -s

# Add binaries to PATH
export PATH=$PWD/bin:$PATH
echo "export PATH=$PWD/bin:$PATH" >> ~/.bashrc
source ~/.bashrc
```
### Node1: CA + Orderer Node Setup
```bash
cd network

# IMPORTANT: Install Hyperledger Fabric binaries first if not done yet
# See section "Install Hyperledger Fabric Binaries (All VMs)" above

# Install npm dependencies for chaincode
cd ../chaincode/ecg_chaincode
npm install
cd ../../network

# Generate crypto-config and distribute to all VMs
./scripts/setup-network.sh

# Create network
./scripts/create-docker-network.sh

# Start CA and Orderer services
docker-compose -f docker-compose-ca-orderer.yaml up -d

# Verify services are running
docker ps
docker logs orderer.example.com
docker logs ca.org1.example.com
```
### Node2: Peer0.Org1 Setup
```bash
cd network

# IMPORTANT: Install Hyperledger Fabric binaries first if not done yet
# See section "Install Hyperledger Fabric Binaries (All VMs)" above

# Create network
./scripts/create-docker-network.sh

# Verify crypto-config received from VM1
ls -la crypto-config/
ls -la channel-artifacts/

# Start peer service
docker-compose -f docker-compose-peer-org1-peer0.yaml up -d

# Verify peer is running
docker ps | grep peer0.org1
docker logs peer0.org1.example.com
```
### Node3: Peer1.Org1 Setup
```bash
cd network

# IMPORTANT: Install Hyperledger Fabric binaries first if not done yet
# See section "Install Hyperledger Fabric Binaries (All VMs)" above

# Create network
./scripts/create-docker-network.sh

# Verify crypto-config received from VM1
ls -la crypto-config/

# Start peer service  
docker-compose -f docker-compose-peer-org1-peer1.yaml up -d

# Verify peer is running
docker ps | grep peer1.org1
docker logs peer1.org1.example.com
```
### Node4: Peer0.Org2 Setup 
```bash
cd network

# IMPORTANT: Install Hyperledger Fabric binaries first if not done yet
# See section "Install Hyperledger Fabric Binaries (All VMs)" above

# Create network
./scripts/create-docker-network.sh

# Verify crypto-config received from VM1
ls -la crypto-config/

# Start peer service
docker-compose -f docker-compose-peer-org2-peer0.yaml up -d

# Verify peer is running
docker ps | grep peer0.org2
docker logs peer0.org2.example.com
```
### Node5: Peer1.Org2 Setup (10.34.1.4)
```bash
cd network

# IMPORTANT: Install Hyperledger Fabric binaries first if not done yet
# See section "Install Hyperledger Fabric Binaries (All VMs)" above

# Create network
./scripts/create-docker-network.sh

# Verify crypto-config received from VM1
ls -la crypto-config/

# Start peer service
docker-compose -f docker-compose-peer-org2-peer1.yaml up -d

# Verify peer is running
docker ps | grep peer1.org2
docker logs peer1.org2.example.com
```
### Node6: Client + IPFS Setup (10.34.1.5)
```bash
# Install Python dependencies
sudo apt install -y python3-pip python3-venv

cd network

# IMPORTANT: Install Hyperledger Fabric binaries first if not done yet
# See section "Install Hyperledger Fabric Binaries (All VMs)" above

# Create network
./scripts/create-docker-network.sh

# Verify crypto-config received from VM1
ls -la crypto-config/

# Start client and IPFS services
docker-compose -f docker-compose-client.yaml up -d

# Verify services
docker ps | grep ipfs
docker ps | grep client
docker logs client.example.com
```
### Create Channel & Deploy Chaincode (Node1)
After all peers are running:
```bash
cd network

# Test connectivity to all peers
ping -c 1 10.34.100.126  # VM2
ping -c 1 10.34.100.128  # VM3  
ping -c 1 10.34.100.114  # VM4
ping -c 1 10.34.100.116  # VM5

# Create channel and join all peers
./scripts/create-channel.sh

# Deploy chaincode to all peers
./scripts/deploy-chaincode.sh

# Verify channel and chaincode
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=10.34.100.126:7051

peer channel list
peer lifecycle chaincode querycommitted --channelID ecgchannel
```
## Demo Workflow

### Required Replacements:
- `GROUP##-PATIENT001`: Unique patient identifier (e.g., `GROUP01-PATIENT001`)
- `Hospital Name`: Your hospital name
- `Dr. Name`: Doctor name
- Patient details: age, gender, symptoms 

**Important:** Each group must use unique patient IDs to avoid data conflicts. Example: GROUP01-PATIENT001, GROUP02-PATIENT001, etc.


### Standard Headers:
- `X-User-Role: admin` - For data upload
- `X-User-Role: patient` - For grant/revoke access
- `X-User-Role: doctor` - For accessing data

### Role Headers:
- `admin`: Upload ECG data
- `patient`: Grant/revoke access, view audit
- `doctor`: Access authorized data

### Step 1: Upload ECG Data (As Admin/Doctor)
```bash
# Replace: PATIENT_ID, patient details
# Note: Use X-User-Role header to simulate different users
curl -H "X-User-Role: admin" -X POST http://10.34.100.125:3000/ecg/upload \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "GROUP##-PATIENT001",
    "ecgData": {
      "patientInfo": {"id": "GROUP##-PATIENT001", "age": 30, "gender": "M", "symptoms": "chest pain"},
      "recordInfo": {"deviceId": "ECG-001", "timestamp": "2025-06-10T10:00:00Z", "samplingRate": 500},
      "leads": {"I": [0.1, 0.2, 0.3], "II": [0.2, 0.3, 0.4]},
      "analysis": {"heartRate": 80, "rhythm": "normal"}
    },
    "metadata": {"hospital": "Hospital Name", "doctor": "Dr. Name", "department": "Cardiology"}
  }' | jq .
```

### Step 2: Wait for Verification
```bash
# Wait 12 seconds for automatic verification to complete
sleep 12 && echo "Verification complete"
```

### Step 3: Grant Access (As Patient)
```bash
# Replace: PATIENT_ID
# Note: Must use X-User-Role: patient header
curl -H "X-User-Role: patient" -X POST http://10.34.100.125:3000/ecg/grant-access \
  -H "Content-Type: application/json" \
  -d '{"patientId": "GROUP##-PATIENT001"}' | jq .
```

### Step 4: Access Data (As Authorized Doctor)
```bash
# Replace: PATIENT_ID
# Note: Use X-User-Role: doctor header
curl -H "X-User-Role: doctor" -X GET http://10.34.100.125:3000/ecg/access/GROUP##-PATIENT001 | jq .
```

### Step 5: Revoke Access (As Patient)
```bash
# Replace: PATIENT_ID
# Note: Must use X-User-Role: patient header
curl -H "X-User-Role: patient" -X POST http://10.34.100.125:3000/ecg/revoke-access \
  -H "Content-Type: application/json" \
  -d '{"patientId": "GROUP##-PATIENT001"}' | jq .
```

### Step 6: Access After Revoke - Should Fail (As Doctor)
```bash
# Replace: PATIENT_ID
# Expected: Access denied error
curl -H "X-User-Role: doctor" -X GET http://10.34.100.125:3000/ecg/access/GROUP##-PATIENT001 | jq .
```

### Step 7: Check Audit Trail (As Patient)
```bash
# Replace: PATIENT_ID
# Note: Shows complete access history
curl -H "X-User-Role: patient" -X GET http://10.34.100.125:3000/ecg/audit/GROUP##-PATIENT001 | jq .
```