from flask import Flask, jsonify, request
import json
import os

from ipfsClient import IPFSClient
from ecgClient import ECGClient

app = Flask(__name__)

# Initialize clients with updated parameters
ipfs_client = IPFSClient(ipfs_host='172.20.1.6', ipfs_port=5001)
ecg_client = ECGClient(
    gateway_endpoint="10.34.100.126:7051",  # VM2 Peer0.Org1
    channel_name='ecgchannel',
    chaincode_name='ecgcc'
)

@app.route('/health', methods=['GET'])
def health_check():
    ipfs_status = ipfs_client.get_status()
    ecg_status = ecg_client.get_connection_info()
    
    return jsonify({
        "status": "UP",
        "ipfs": ipfs_status,
        "blockchain": ecg_status,
        "timestamp": ecg_status.get("timestamp")
    })

@app.route('/ecg/upload', methods=['POST'])
def upload_ecg():
    """Upload ECG data to IPFS and store metadata on blockchain"""
    try:
        # Get request data
        data = request.json
        patient_id = data.get('patientId')
        ecg_data = data.get('ecgData')
        metadata = data.get('metadata', {})
        
        if not patient_id or not ecg_data:
            return jsonify({"error": "Missing required fields: patientId, ecgData"}), 400
        
        # Upload to IPFS
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)
        
        # Store metadata on blockchain
        blockchain_result = ecg_client.store_ecg_data(patient_id, ipfs_hash, metadata)
        
        return jsonify({
            "status": "success",
            "ipfsHash": ipfs_hash,
            "blockchainResponse": blockchain_result,
            "patientId": patient_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg(patient_id):
    """Access ECG data for a patient"""
    try:
        # Get ECG metadata from blockchain
        blockchain_result = ecg_client.access_ecg_data(patient_id)
        
        # Get actual ECG data from IPFS
        ipfs_hash = blockchain_result.get('ipfsHash')
        if ipfs_hash:
            ecg_data = ipfs_client.get_ecg_data(ipfs_hash)
        else:
            ecg_data = {"note": "No IPFS hash available"}
        
        return jsonify({
            "status": "success",
            "metadata": blockchain_result,
            "ecgData": ecg_data,
            "patientId": patient_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/grant-access', methods=['POST'])
def grant_access():
    """Grant access to a user for a patient's ECG data"""
    try:
        # Get request data
        data = request.json
        patient_id = data.get('patientId')
        user_id = data.get('userId')
        
        if not patient_id or not user_id:
            return jsonify({"error": "Missing required fields: patientId, userId"}), 400
        
        # Grant access via blockchain
        result = ecg_client.grant_access(patient_id, user_id)
        
        return jsonify({
            "status": "success",
            "response": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/revoke-access', methods=['POST'])
def revoke_access():
    """Revoke access from a user for a patient's ECG data"""
    try:
        # Get request data
        data = request.json
        patient_id = data.get('patientId')
        user_id = data.get('userId')
        
        if not patient_id or not user_id:
            return jsonify({"error": "Missing required fields: patientId, userId"}), 400
        
        # Revoke access via blockchain
        result = ecg_client.revoke_access(patient_id, user_id)
        
        return jsonify({
            "status": "success",
            "response": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/audit/<patient_id>', methods=['GET'])
def get_audit_trail(patient_id):
    """Get the audit trail for a patient's ECG data"""
    try:
        # Get audit trail from blockchain
        result = ecg_client.get_audit_trail(patient_id)
        
        return jsonify({
            "status": "success",
            "auditTrail": result,
            "patientId": patient_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed system status"""
    try:
        return jsonify({
            "ipfs": ipfs_client.get_status(),
            "blockchain": ecg_client.get_connection_info(),
            "endpoints": {
                "health": "/health",
                "upload": "/ecg/upload",
                "access": "/ecg/access/<patient_id>",
                "grant": "/ecg/grant-access",
                "revoke": "/ecg/revoke-access", 
                "audit": "/ecg/audit/<patient_id>"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting ECG Blockchain Client...")
    print("📋 Available endpoints:")
    print("  - GET  /health")
    print("  - GET  /status") 
    print("  - POST /ecg/upload")
    print("  - GET  /ecg/access/<patient_id>")
    print("  - POST /ecg/grant-access")
    print("  - POST /ecg/revoke-access")
    print("  - GET  /ecg/audit/<patient_id>")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
