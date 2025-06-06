#!/bin/bash

set -e

echo "=== ECG Chaincode Deployment Script ==="

# VM IP Addresses
VM1_IP="10.34.100.121"  # Orderer
VM2_IP="10.34.100.126"  # Peer0.Org1
VM3_IP="10.34.100.128"  # Peer1.Org1  
VM4_IP="10.34.100.114"  # Peer0.Org2
VM5_IP="10.34.100.116"  # Peer1.Org2

# Chaincode configuration
export FABRIC_CFG_PATH=${PWD}
export CORE_PEER_TLS_ENABLED=true
export CHANNEL_NAME=ecgchannel
export CC_NAME=ecgcontract
export CC_SRC_PATH=../chaincode/ecg_chaincode
export CC_VERSION=1.4
export CC_SEQUENCE=2

ORDERER_TLS_ROOTCERT_FILE_FOR_CLIENT="${PWD}/crypto-config/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem"

# Parse command line arguments
CLEAN_START=false
FORCE_REINSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_START=true
            shift
            ;;
        --force-reinstall)
            FORCE_REINSTALL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--force-reinstall]"
            echo "  --clean: Start from beginning, remove existing approvals"
            echo "  --force-reinstall: Reinstall chaincode even if already installed"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to test peer connectivity
test_peer_connectivity() {
    local peer_name=$1
    local peer_ip=$2
    local peer_port=$3
    
    if nc -z $peer_ip $peer_port 2>/dev/null; then
        log_info "✓ $peer_name ($peer_ip:$peer_port) is reachable"
        return 0
    else
        log_error "✗ $peer_name ($peer_ip:$peer_port) is not reachable"
        return 1
    fi
}

# Function to test orderer connectivity
test_orderer_connectivity() {
    if nc -z $VM1_IP 7050 2>/dev/null; then
        log_info "✓ Orderer ($VM1_IP:7050) is reachable"
        return 0
    else
        log_error "✗ Orderer ($VM1_IP:7050) is not reachable"
        return 1
    fi
}

# Function to check if peer has joined channel
check_peer_channel() {
    local peer_name=$1
    local msp_id=$2
    local peer_ip=$3
    local peer_port=$4
    
    # Set environment for the peer
    export CORE_PEER_LOCALMSPID="$msp_id"
    if [[ $msp_id == "Org1MSP" ]]; then
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    else
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
    fi
    export CORE_PEER_ADDRESS=$peer_ip:$peer_port
    
    if peer channel list 2>/dev/null | grep -q $CHANNEL_NAME; then
        log_info "✓ $peer_name has joined channel $CHANNEL_NAME"
        return 0
    else
        log_warn "✗ $peer_name has NOT joined channel $CHANNEL_NAME"
        return 1
    fi
}

# Function to join peer to channel if not already joined
join_peer_to_channel() {
    local peer_name=$1
    local msp_id=$2
    local peer_ip=$3
    local peer_port=$4
    
    log_info "Attempting to join $peer_name to channel..."
    
    # Set environment
    export CORE_PEER_LOCALMSPID="$msp_id"
    if [[ $msp_id == "Org1MSP" ]]; then
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    else
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
    fi
    export CORE_PEER_ADDRESS=$peer_ip:$peer_port
    
    if peer channel join -b ./channel-artifacts/${CHANNEL_NAME}.block; then
        log_info "✓ $peer_name joined channel successfully"
        return 0
    else
        log_error "✗ Failed to join $peer_name to channel"
        return 1
    fi
}

# Function to install chaincode on peer
install_chaincode_on_peer() {
    local peer_name=$1
    local msp_id=$2
    local peer_ip=$3
    local peer_port=$4
    
    # Set environment
    export CORE_PEER_LOCALMSPID="$msp_id"
    if [[ $msp_id == "Org1MSP" ]]; then
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    else
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
    fi
    export CORE_PEER_ADDRESS=$peer_ip:$peer_port
    
    # Check if already installed
    if [[ $FORCE_REINSTALL == false ]] && peer lifecycle chaincode queryinstalled 2>/dev/null | grep -q "${CC_NAME}_${CC_VERSION}"; then
        log_info "✓ Chaincode already installed on $peer_name, skipping..."
        return 0
    fi
    
    log_info "Installing chaincode on $peer_name..."
    if peer lifecycle chaincode install ${CC_NAME}.tar.gz; then
        log_info "✓ Chaincode installed on $peer_name"
        return 0
    else
        log_error "✗ Failed to install chaincode on $peer_name"
        return 1
    fi
}

# Function to approve chaincode for organization
# Function to approve chaincode for organization
approve_chaincode_for_org() {
    local org_name=$1
    local msp_id=$2
    local peer_ip=$3
    local peer_port=$4
    local package_id=$5

    # Set environment
    export CORE_PEER_LOCALMSPID="$msp_id"
    if [[ $msp_id == "Org1MSP" ]]; then
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    else
        export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
        export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
    fi
    export CORE_PEER_ADDRESS=$peer_ip:$peer_port

    # Logika untuk melewati approval jika sudah ada (bahkan dengan --clean) jika errornya adalah "redefine"
    # Ini hanya workaround untuk kasus spesifik Anda sekarang.
     if [[ $CLEAN_START == false ]]; then
         log_info "Checking if $org_name already approved..."
         if peer lifecycle chaincode checkcommitreadiness \
             --channelID ${CHANNEL_NAME} \
             --name ${CC_NAME} \
             --version ${CC_VERSION} \
             --sequence ${CC_SEQUENCE} \
             --init-required \
             --output json 2>/dev/null | grep -q "\"$msp_id\": true"; then
             log_info "✓ $org_name already approved (from checkcommitreadiness), skipping..."
             return 0
         fi
     fi

    log_info "Attempting to approve chaincode for $org_name..."
    if output=$(peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --channelID ${CHANNEL_NAME} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --package-id ${package_id} \
        --sequence ${CC_SEQUENCE} \
        --init-required \
        --tls \
        --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem 2>&1); then
        log_info "✓ $org_name approved chaincode successfully."
        return 0
    else
        # Periksa apakah errornya karena "redefine uncommitted sequence" dan CC_SEQUENCE adalah 1
        if [[ "$output" == *"attempted to redefine uncommitted sequence ("${CC_SEQUENCE}") for namespace ${CC_NAME} with unchanged content"* ]]; then
            log_warn "✓ $org_name ($msp_id) already has a pending approval for sequence ${CC_SEQUENCE} with identical content. Proceeding..."
            return 0 # Anggap sukses jika errornya adalah ini
        else
            log_error "✗ Failed to approve chaincode for $org_name. Output:"
            echo "$output"
            return 1
        fi
    fi
}

# Main execution starts here
log_info "Starting chaincode deployment..."

if [[ $CLEAN_START == true ]]; then
    log_warn "Clean start mode: Will restart approval process from beginning"
fi

# Step 1: Test connectivity
log_info "=== Step 1: Testing Connectivity ==="
test_orderer_connectivity || exit 1
test_peer_connectivity "peer0.org1" $VM2_IP 7051 || exit 1
test_peer_connectivity "peer1.org1" $VM3_IP 8051 || exit 1
test_peer_connectivity "peer0.org2" $VM4_IP 9051 || exit 1
test_peer_connectivity "peer1.org2" $VM5_IP 10051 || exit 1

# Di awal skrip, setelah parsing argumen atau sebelum Step 2
if [[ $FORCE_REINSTALL == true ]] || [[ APAKAH_ADA_PERUBAHAN_KODE_ATAU_VERSI == true ]]; then # Logika ini perlu Anda pikirkan implementasinya
    log_info "Removing old chaincode package ${CC_NAME}.tar.gz to force repackaging..."
    rm -f ./${CC_NAME}.tar.gz
fi

# Kemudian Step 2 akan membuat ulang jika file tidak ada
log_info "=== Step 2: Packaging Chaincode ==="
if [[ ! -f "${CC_NAME}.tar.gz" ]]; then # Selalu package jika file tidak ada (karena baru dihapus)
    log_info "Packaging chaincode ${CC_NAME} version ${CC_VERSION}..."
    peer lifecycle chaincode package ${CC_NAME}.tar.gz \
        --path ${CC_SRC_PATH} \
        --lang node \
        --label ${CC_NAME}_${CC_VERSION} # Menggunakan CC_VERSION saat ini
    log_info "✓ Chaincode packaged"
else
    log_info "✓ Chaincode package ${CC_NAME}.tar.gz already exists and not forcing repackage."
fi

# Step 3: Check channel membership
log_info "=== Step 3: Checking Channel Membership ==="
check_peer_channel "peer0.org1" "Org1MSP" $VM2_IP 7051 || join_peer_to_channel "peer0.org1" "Org1MSP" $VM2_IP 7051 || exit 1
check_peer_channel "peer1.org1" "Org1MSP" $VM3_IP 8051 || join_peer_to_channel "peer1.org1" "Org1MSP" $VM3_IP 8051 || exit 1
check_peer_channel "peer0.org2" "Org2MSP" $VM4_IP 9051 || join_peer_to_channel "peer0.org2" "Org2MSP" $VM4_IP 9051 || exit 1
check_peer_channel "peer1.org2" "Org2MSP" $VM5_IP 10051 || join_peer_to_channel "peer1.org2" "Org2MSP" $VM5_IP 10051 || exit 1

# Step 4: Install chaincode
log_info "=== Step 4: Installing Chaincode ==="
install_chaincode_on_peer "peer0.org1" "Org1MSP" $VM2_IP 7051 || exit 1
install_chaincode_on_peer "peer1.org1" "Org1MSP" $VM3_IP 8051 || exit 1
install_chaincode_on_peer "peer0.org2" "Org2MSP" $VM4_IP 9051 || exit 1
install_chaincode_on_peer "peer1.org2" "Org2MSP" $VM5_IP 10051 || exit 1

# Step 5: Get package ID
log_info "=== Step 5: Getting Package ID ==="
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=$VM2_IP:7051

PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep ${CC_NAME}_${CC_VERSION} | awk '{print $3}' | cut -d ',' -f1)
if [[ -z "$PACKAGE_ID" ]]; then
    log_error "Failed to get package ID"
    exit 1
fi
log_info "Package ID: $PACKAGE_ID"

# Step 6: Approve chaincode
log_info "=== Step 6: Approving Chaincode ==="
approve_chaincode_for_org "Org1" "Org1MSP" $VM2_IP 7051 "$PACKAGE_ID" || exit 1
approve_chaincode_for_org "Org2" "Org2MSP" $VM4_IP 9051 "$PACKAGE_ID" || exit 1

# Step 7: Check commit readiness
log_info "=== Step 7: Checking Commit Readiness ==="
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=$VM2_IP:7051

COMMIT_READINESS=$(peer lifecycle chaincode checkcommitreadiness \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --init-required \
    --output json)

echo "$COMMIT_READINESS"

if echo "$COMMIT_READINESS" | grep -q '"Org1MSP": true' && echo "$COMMIT_READINESS" | grep -q '"Org2MSP": true'; then
    log_info "✓ Both organizations approved - ready to commit"
else
    log_error "✗ Not all organizations approved"
    echo "Commit readiness status: $COMMIT_READINESS"
    exit 1
fi

# Step 8: Commit chaincode
log_info "=== Step 8: Committing Chaincode ==="

NEEDS_COMMIT=true
# Set konteks untuk querycommitted (misalnya ke peer0.org1)
# (Variabel lingkungan untuk Org1 Admin seharusnya sudah terset dari CheckCommitReadiness)

COMMITTED_CC_INFO_JSON=$(peer lifecycle chaincode querycommitted --channelID ${CHANNEL_NAME} --name ${CC_NAME} --output json 2>/dev/null)

if [[ $? -eq 0 && -n "$COMMITTED_CC_INFO_JSON" ]] && echo "$COMMITTED_CC_INFO_JSON" | jq '.sequence' &> /dev/null; then
    COMMITTED_SEQUENCE=$(echo "$COMMITTED_CC_INFO_JSON" | jq -r '.sequence')
    log_info "Currently committed sequence for ${CC_NAME} is ${COMMITTED_SEQUENCE}. Requested sequence is ${CC_SEQUENCE}."

    if [[ "$COMMITTED_SEQUENCE" == "$CC_SEQUENCE" ]]; then
        log_info "✓ Chaincode ${CC_NAME} with sequence ${CC_SEQUENCE} already committed."
        NEEDS_COMMIT=false
    elif [[ "$COMMITTED_SEQUENCE" -gt "$CC_SEQUENCE" ]]; then
        log_error "✗ Error: A newer sequence (${COMMITTED_SEQUENCE}) of chaincode ${CC_NAME} is already committed. Current attempt is for sequence ${CC_SEQUENCE}."
        exit 1
    else
        log_info "Found older committed sequence ${COMMITTED_SEQUENCE}. Proceeding to commit new sequence ${CC_SEQUENCE}."
    fi
else
    log_info "No committed chaincode definition found for ${CC_NAME} or failed to parse. Proceeding to commit sequence ${CC_SEQUENCE}."
fi

if [[ "$NEEDS_COMMIT" == true ]]; then
    log_info "Committing chaincode ${CC_NAME} version ${CC_VERSION} sequence ${CC_SEQUENCE}..."
    # Pastikan konteks Admin Org1 masih aktif untuk menjalankan commit
    export CORE_PEER_LOCALMSPID="Org1MSP"
    export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    export CORE_PEER_MSPCONFIGPATH=${PWD}/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    export CORE_PEER_ADDRESS=$VM2_IP:7051 # Peer yang digunakan untuk mengirim proposal commit

    peer lifecycle chaincode commit -o $VM1_IP:7050 \
        --ordererTLSHostnameOverride orderer.example.com \
        --channelID ${CHANNEL_NAME} \
        --name ${CC_NAME} \
        --version ${CC_VERSION} \
        --sequence ${CC_SEQUENCE} \
        --init-required \
        --tls \
        --cafile "${ORDERER_TLS_ROOTCERT_FILE_FOR_CLIENT}" \
        --peerAddresses $VM2_IP:7051 \
        --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
        --peerAddresses $VM4_IP:9051 \
        --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt 
 
    if [[ $? -eq 0 ]]; then
        log_info "✓ Chaincode committed successfully."
        # Jika commit sukses, maka Langkah 9 (Init) mungkin perlu dijalankan (tidak dikomentari)
    else
        log_error "✗ Failed to commit chaincode."
        exit 1
    fi
fi

# Step 9: Initialize chaincode
log_info "=== Step 9: Initializing Chaincode ==="
log_info "Initializing chaincode..."
peer chaincode invoke -o orderer.example.com:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls \
    --cafile ${PWD}/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    -C ${CHANNEL_NAME} \
    -n ${CC_NAME} \
    --isInit \
    -c '{"function":"initLedger","Args":[]}' \
    --peerAddresses $VM2_IP:7051 \
    --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses $VM4_IP:9051 \
    --tlsRootCertFiles ${PWD}/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

log_info "✓ Chaincode initialized"

# Step 10: Verify deployment
log_info "=== Step 10: Verifying Deployment ==="
peer lifecycle chaincode querycommitted --channelID ${CHANNEL_NAME}

log_info "🎉 Chaincode deployment completed successfully!"
log_info "Chaincode '$CC_NAME' version '$CC_VERSION' is now ready for use on channel '$CHANNEL_NAME'"
