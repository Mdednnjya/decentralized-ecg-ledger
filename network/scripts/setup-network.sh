#!/bin/bash

set -e

echo "=== Setup Hyperledger Fabric Network ==="

# VM IP Addresses
VM1_IP="10.34.100.121"  # CA + Orderer (kel3)
VM2_IP="10.34.100.126"  # Peer0.Org1 (kel5)
VM3_IP="10.34.100.128"  # Peer1.Org1 (kel6)
VM4_IP="10.34.100.114"  # Peer0.Org2 (kel1)
VM5_IP="10.34.100.116"  # Peer1.Org2 (kel2)
VM6_IP="10.34.100.125"  # Client + IPFS (kel4)

# Usernames for each VM based on group number
USER_VM2="group5" # Sesuai dengan (kel5)
USER_VM3="group6" # Sesuai dengan (kel6)
USER_VM4="group1" # Sesuai dengan (kel1)
USER_VM5="group2" # Sesuai dengan (kel2)
USER_VM6="group4" # Sesuai dengan (kel4)
# USER_VM1="group3" # Untuk VM1 (kel3),

echo "Network topology:"
echo "VM1 ($VM1_IP): CA + Orderer (User: group3)"
echo "VM2 ($VM2_IP): Peer0.Org1 (User: $USER_VM2)"
echo "VM3 ($VM3_IP): Peer1.Org1 (User: $USER_VM3)"
echo "VM4 ($VM4_IP): Peer0.Org2 (User: $USER_VM4)"
echo "VM5 ($VM5_IP): Peer1.Org2 (User: $USER_VM5)"
echo "VM6 ($VM6_IP): Client + IPFS (User: $USER_VM6)"

echo ""
echo "Step 1: Generate crypto material and artifacts..."
./scripts/generate-artifacts.sh

echo ""
echo "Step 2: Update connection profiles with actual IPs..."
# Update connection profiles
sed -i "s/10.34.1.1/$VM2_IP/g" ../client/config/connection-org1.json
sed -i "s/10.34.1.2/$VM3_IP/g" ../client/config/connection-org1.json
sed -i "s/10.34.1.3/$VM4_IP/g" ../client/config/connection-org1.json
sed -i "s/10.34.1.4/$VM5_IP/g" ../client/config/connection-org1.json
sed -i "s/10.34.1.10/$VM1_IP/g" ../client/config/connection-org1.json

sed -i "s/10.34.1.1/$VM2_IP/g" ../client/config/connection-org2.json
sed -i "s/10.34.1.2/$VM3_IP/g" ../client/config/connection-org2.json
sed -i "s/10.34.1.3/$VM4_IP/g" ../client/config/connection-org2.json
sed -i "s/10.34.1.4/$VM5_IP/g" ../client/config/connection-org2.json
sed -i "s/10.34.1.10/$VM1_IP/g" ../client/config/connection-org2.json
echo "Connection profiles updated."

echo ""
echo "Step 3: Test connectivity to all VMs..."
for ip in $VM2_IP $VM3_IP $VM4_IP $VM5_IP $VM6_IP; do
    if ping -c 1 $ip >/dev/null 2>&1; then
        echo "✓ VM $ip reachable"
    else
        echo "✗ VM $ip unreachable"
        exit 1
    fi
done
echo "Connectivity test passed."

echo ""
echo "Step 4: Distribute crypto-config to all VMs..."

# VM2 (kel5)
echo "Copying to VM: $VM2_IP (User: $USER_VM2)"
scp -r ./crypto-config ${USER_VM2}@${VM2_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy crypto-config to $VM2_IP"
scp -r ./channel-artifacts ${USER_VM2}@${VM2_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy channel-artifacts to $VM2_IP"

# VM3 (kel6)
echo "Copying to VM: $VM3_IP (User: $USER_VM3)"
scp -r ./crypto-config ${USER_VM3}@${VM3_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy crypto-config to $VM3_IP"
scp -r ./channel-artifacts ${USER_VM3}@${VM3_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy channel-artifacts to $VM3_IP"

# VM4 (kel1)
echo "Copying to VM: $VM4_IP (User: $USER_VM4)"
scp -r ./crypto-config ${USER_VM4}@${VM4_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy crypto-config to $VM4_IP"
scp -r ./channel-artifacts ${USER_VM4}@${VM4_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy channel-artifacts to $VM4_IP"

# VM5 (kel2)
echo "Copying to VM: $VM5_IP (User: $USER_VM5)"
scp -r ./crypto-config ${USER_VM5}@${VM5_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy crypto-config to $VM5_IP"
scp -r ./channel-artifacts ${USER_VM5}@${VM5_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy channel-artifacts to $VM5_IP"

# VM6 (kel4)
echo "Copying to VM: $VM6_IP (User: $USER_VM6)"
scp -r ./crypto-config ${USER_VM6}@${VM6_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy crypto-config to $VM6_IP"
scp -r ./channel-artifacts ${USER_VM6}@${VM6_IP}:~/decentralized-ecg-ledger/network/ || echo "Failed to copy channel-artifacts to $VM6_IP"

echo ""
echo "✓ Setup completed!"