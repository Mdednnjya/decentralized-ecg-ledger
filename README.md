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
# Create directory for Fabric binaries
mkdir -p $HOME/fabric-binaries

# Download Fabric binaries
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.5 -d -s

# Add binaries to PATH
export PATH=$HOME/fabric-binaries/bin:$PATH
echo 'export PATH=$HOME/fabric-binaries/bin:$PATH' >> ~/.bashrc
```
### VM1: Orderer Node Setup (10.34.1.10)
```bash
cd network

# Generate crypto material and channel artifacts
./scripts/generate-artifacts.sh

# Set up docker network
docker network create --subnet=10.34.1.0/24 ecg_network

# Start the orderer
docker-compose -f docker-compose-orderer.yaml up -d

# Check if container is running
docker ps | grep orderer
```
### VM2: Peer0.Org1 Setup (10.34.1.1)
```bash
cd network

# Set up docker network
docker network create --subnet=10.34.1.0/24 ecg_network

# Copy crypto material and channel artifacts from VM1
# (In a real scenario, use scp or another secure method to copy files)
# scp -r user@10.34.1.10:~/decentralized-ecg-ledger/network/crypto-config .
# scp -r user@10.34.1.10:~/decentralized-ecg-ledger/network/channel-artifacts .

# Start the peer
docker-compose -f docker-compose-peer-org1-peer0.yaml up -d

# Check if containers are running
docker ps | grep peer0.org1

# Create the channel (after all peers are up)
./scripts/create-channel.sh

# Deploy chaincode (after channel is created)
./scripts/deploy-chaincode.sh
```
### VM3: Peer1.Org1 Setup (10.34.1.2)
```bash
cd network

# Set up docker network
docker network create --subnet=10.34.1.0/24 ecg_network

# Copy crypto material from VM1 (as in VM2 setup)

# Start the peer
docker-compose -f docker-compose-peer-org1-peer1.yaml up -d

# Check if containers are running
docker ps | grep peer1.org1
```
### VM4: Peer0.Org2 Setup (10.34.1.3)
```bash
cd network

# Set up docker network
docker network create --subnet=10.34.1.0/24 ecg_network

# Copy crypto material from VM1 (as in VM2 setup)

# Start the peer
docker-compose -f docker-compose-peer-org2-peer0.yaml up -d

# Check if containers are running
docker ps | grep peer0.org2
```
### VM5: Peer1.Org2 Setup (10.34.1.4)
```bash
cd network

# Set up docker network
docker network create --subnet=10.34.1.0/24 ecg_network

# Copy crypto material from VM1 (as in VM2 setup)

# Start the peer
docker-compose -f docker-compose-peer-org2-peer1.yaml up -d

# Check if containers are running
docker ps | grep peer1.org2
```
### VM6: Client + IPFS Setup (10.34.1.5)
```bash
# Set up docker network
docker network create --subnet=10.34.1.0/24 ecg_network

# Install additional requirements for the client node
sudo apt install -y python3-pip python3-venv nodejs npm

# Install IPFS
wget https://dist.ipfs.io/go-ipfs/v0.18.1/go-ipfs_v0.18.1_linux-amd64.tar.gz
tar -xvzf go-ipfs_v0.18.1_linux-amd64.tar.gz
cd go-ipfs
sudo bash install.sh
cd ..
rm -rf go-ipfs*

# Initialize IPFS
ipfs init
# Configure IPFS to allow API access from other hosts
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '["PUT", "POST", "GET"]'

# Start IPFS daemon in the background
ipfs daemon &

# Copy crypto material from VM1 (as in VM2 setup)

# Set up Python environment for the client
cd client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the client application
cd app
python webapp.py
```
## Detailed Usage Instructions

### 1. Upload ECG Data

This can be done via the REST API from VM6:

```bash
curl -X POST http://10.34.1.5:3000/ecg/upload \
 -H "Content-Type: application/json" \
 -d '{
   "patientId": "PAT001",
   "ecgData": {
     "patientInfo": {
       "id": "PAT001",
       "age": 45,
       "gender": "M"
     },
     "recordInfo": {
       "deviceId": "ECG-DEVICE-001",
       "timestamp": "2025-05-15T12:00:00Z",
       "samplingRate": 500
     },
     "leads": {
       "I": [0.1, 0.2, 0.5, 0.7, 0.8],
       "II": [0.2, 0.3, 0.6, 0.8, 0.9]
     }
   },
   "metadata": {
     "hospital": "General Hospital",
     "doctor": "Dr. Smith"
   }
 }'
```
Or use a Python script:
```bash
import requests
import json

# Load sample ECG data
with open('../sample-data/sample_ecg.json', 'r') as file:
    sample_ecg = json.load(file)

# Upload ECG data
response = requests.post(
    'http://localhost:3000/ecg/upload',
    json={
        'patientId': 'PAT001',
        'ecgData': sample_ecg,
        'metadata': {
            'hospital': 'General Hospital',
            'doctor': 'Dr. Smith'
        }
    }
)
print("Upload response:", response.json())
```
### 2. Grant Access to Another User

```bash
curl -X POST http://10.34.1.5:3000/ecg/grant-access \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "PAT001",
    "userId": "DR001"
  }'
```
Python Example:
```bash
response = requests.post(
    'http://localhost:3000/ecg/grant-access',
    json={
        'patientId': 'PAT001',
        'userId': 'DR001'
    }
)
print("Grant access response:", response.json())
```
### 3. Revoke Access from a User

```bash
curl -X POST http://10.34.1.5:3000/ecg/revoke-access \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "PAT001",
    "userId": "DR001"
  }'
```
Python Example:
```bash
response = requests.post(
    'http://localhost:3000/ecg/revoke-access',
    json={
        'patientId': 'PAT001',
        'userId': 'DR001'
    }
)
print("Revoke access response:", response.json())
```
### 4. Access ECG Data

```bash
curl -X GET http://10.34.1.5:3000/ecg/access/PAT001
```
Python Example:
```bash
response = requests.get('http://localhost:3000/ecg/access/PAT001')
print("Access response:", response.json())

# If the access was successful, you can extract the ECG data
if response.status_code == 200:
    result = response.json()
    ecg_data = result['ecgData']
    print("Heart rate:", ecg_data['analysis']['heartRate'])
```
### 5. View Audit Trail

```bash
curl -X GET http://10.34.1.5:3000/ecg/audit/PAT001
```
Python Example:
```bash
response = requests.get('http://localhost:3000/ecg/audit/PAT001')
print("Audit trail:", response.json())

# Process the audit trail
if response.status_code == 200:
    audit_trail = response.json()['auditTrail']
    for access in audit_trail:
        print(f"Accessed by {access['accessorID']} at {access['timestamp']}")
```
### 2. Grant Access to Another User

```bash
curl -X POST http://10.34.1.5:3000/ecg/grant-access \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "PAT001",
    "userId": "DR001"
  }'
```
Python Example:
```bash
response = requests.post(
    'http://localhost:3000/ecg/grant-access',
    json={
        'patientId': 'PAT001',
        'userId': 'DR001'
    }
)
print("Grant access response:", response.json())
```