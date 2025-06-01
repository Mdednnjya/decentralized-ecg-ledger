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

echo "Network topology:"
echo "VM1 ($VM1_IP): CA + Orderer"
echo "VM2 ($VM2_IP): Peer0.Org1"
echo "VM3 ($VM3_IP): Peer1.Org1" 
echo "VM4 ($VM4_IP): Peer0.Org2"
echo "VM5 ($VM5_IP): Peer1.Org2"
echo "VM6 ($VM6_IP): Client + IPFS"

echo "Step 1: Generate crypto material and artifacts..."
./generate-artifacts.sh

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

echo "Step 3: Test connectivity to all VMs..."
for ip in $VM2_IP $VM3_IP $VM4_IP $VM5_IP $VM6_IP; do
    if ping -c 1 $ip >/dev/null 2>&1; then
        echo "✓ VM $ip reachable"
    else
        echo "✗ VM $ip unreachable"
        exit 1
    fi
done

echo "Step 4: Distribute crypto-config to all VMs..."
for ip in $VM2_IP $VM3_IP $VM4_IP $VM5_IP $VM6_IP; do
    echo "Copying to VM: $ip"
    scp -r ../crypto-config student@$ip:~/decentralized-ecg-ledger/network/ || echo "Failed to copy to $ip"
    scp -r ../channel-artifacts student@$ip:~/decentralized-ecg-ledger/network/ || echo "Failed to copy to $ip"
done

echo "✓ Setup completed!"
