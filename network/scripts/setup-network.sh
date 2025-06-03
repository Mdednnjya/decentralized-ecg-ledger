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

# Base remote project path (default)
REMOTE_PROJECT_BASE_PATH="decentralized-ecg-ledger"

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
echo "Step 4: Clean old artifacts and distribute crypto-config to all VMs..."

# Function to clean and copy artifacts
# Parameter 4: Optional remote project base path override
distribute_to_vm() {
    local vm_ip=$1
    local vm_user=$2
    local vm_desc=$3
    local remote_base_path_override=$4
    local remote_path_to_network

    if [ -n "$remote_base_path_override" ]; then
        remote_path_to_network="${remote_base_path_override}/network"
    else
        remote_path_to_network="${REMOTE_PROJECT_BASE_PATH}/network"
    fi

    echo "Distributing to VM: $vm_ip ($vm_desc) at ~/${remote_path_to_network}"

    # Ensure parent directories exist and then remove old artifacts on remote VM first
    echo "  - Ensuring directory structure and removing old crypto-config and channel-artifacts on $vm_ip..."
    ssh ${vm_user}@${vm_ip} "mkdir -p ~/${remote_path_to_network} && cd ~/${remote_path_to_network} && rm -rf crypto-config/ channel-artifacts/" || echo "  Warning: Failed to setup directories or remove old artifacts on $vm_ip"

    # Copy new artifacts
    echo "  - Copying new crypto-config to $vm_ip..."
    scp -r ./crypto-config ${vm_user}@${vm_ip}:~/${remote_path_to_network}/ || echo "  Failed to copy crypto-config to $vm_ip"

    echo "  - Copying new channel-artifacts to $vm_ip..."
    scp -r ./channel-artifacts ${vm_user}@${vm_ip}:~/${remote_path_to_network}/ || echo "  Failed to copy channel-artifacts to $vm_ip"

    echo "  ✓ Distribution to $vm_ip completed"
}

# VM2 (kel5) - Default path
distribute_to_vm "$VM2_IP" "$USER_VM2" "User: $USER_VM2"

# VM3 (kel6) - Default path
distribute_to_vm "$VM3_IP" "$USER_VM3" "User: $USER_VM3"

# VM4 (kel1) - Custom path: ~/ecg/decentralized-ecg-ledger/network
distribute_to_vm "$VM4_IP" "$USER_VM4" "User: $USER_VM4" "ecg/${REMOTE_PROJECT_BASE_PATH}"

# VM5 (kel2) - Default path
distribute_to_vm "$VM5_IP" "$USER_VM5" "User: $USER_VM5"

# VM6 (kel4) - Default path
distribute_to_vm "$VM6_IP" "$USER_VM6" "User: $USER_VM6"

echo ""
echo "✓ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Start services on VM1: docker-compose -f docker-compose-ca-orderer.yaml up -d"
echo "2. Start peer services on VM2-5"
echo "3. Start client on VM6"
echo "4. Create channel from VM1: ./scripts/create-channel.sh"