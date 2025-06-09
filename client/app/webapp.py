from flask import Flask, jsonify, request
import json
import os
from datetime import datetime

from ipfsClient import IPFSClient
from fabricGatewayClient import FabricGatewayClient

app = Flask(__name__)

# Initialize clients
ipfs_client = IPFSClient(ipfs_host='172.20.1.6', ipfs_port=5001)
fabric_client = FabricGatewayClient(peer_address="10.34.100.126:7051")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    ipfs_status = ipfs_client.get_status()
    fabric_info = fabric_client.get_connection_info()
    
    return jsonify({
        "status": "UP",
        "ipfs": ipfs_status,
        "blockchain": fabric_info,
        "escrowPattern": "ENABLED",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/ecg/upload', methods=['POST'])
def upload_ecg():
    """Upload ECG data - Case: Dr. Sarah menyimpan ECG Maria"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        ecg_data = data.get('ecgData')
        metadata = data.get('metadata', {})
        patient_owner_id = data.get('patientOwnerClientID', f'x509::CN={patient_id}')
        
        if not patient_id or not ecg_data:
            return jsonify({"error": "Missing required fields: patientId, ecgData"}), 400
        
        # Upload to IPFS
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)
        
        # Store to blockchain
        blockchain_result = fabric_client.store_ecg_data(patient_id, ipfs_hash, metadata, patient_owner_id)
        
        return jsonify({
            "status": "success",
            "message": "ECG data uploaded successfully",
            "patientId": patient_id,
            "ipfsHash": ipfs_hash,
            "blockchainResult": blockchain_result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/grant-access', methods=['POST'])
def grant_access():
    """Grant access - Case: Maria memberikan akses ke Dr. Ahmad"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID')
        
        if not patient_id or not doctor_id:
            return jsonify({"error": "Missing patientId or doctorClientID"}), 400
        
        result = fabric_client.grant_access(patient_id, doctor_id)
        
        return jsonify({
            "status": "success",
            "message": "Access granted for second opinion",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/revoke-access', methods=['POST'])
def revoke_access():
    """Revoke access - Case: Maria mencabut akses Dr. Ahmad"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID')
        
        if not patient_id or not doctor_id:
            return jsonify({"error": "Missing patientId or doctorClientID"}), 400
        
        result = fabric_client.revoke_access(patient_id, doctor_id)
        
        return jsonify({
            "status": "success",
            "message": "Access revoked after consultation",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg(patient_id):
    """Access ECG data - Case: Dr. Ahmad mengakses data Maria"""
    try:
        result = fabric_client.access_ecg_data(patient_id)
        
        if 'error' in result:
            return jsonify(result), 403
        
        return jsonify({
            "status": "success",
            "message": "ECG data accessed successfully",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/audit/<patient_id>', methods=['GET'])
def get_audit_trail(patient_id):
    """Get audit trail - Case: Transparansi aktivitas Maria"""
    try:
        result = fabric_client.get_audit_trail(patient_id)
        
        return jsonify({
            "status": "success",
            "message": "Audit trail retrieved successfully",
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting ECG Blockchain System...")
    print("📋 Available endpoints:")
    print("  - POST /ecg/upload (Dr. Sarah stores Maria's ECG)")
    print("  - POST /ecg/grant-access (Maria grants access to Dr. Ahmad)")
    print("  - GET  /ecg/access/<patient_id> (Dr. Ahmad accesses ECG)")
    print("  - POST /ecg/revoke-access (Maria revokes access)")
    print("  - GET  /ecg/audit/<patient_id> (View audit trail)")
    print("\n⛓️  Blockchain: Hyperledger Fabric")
    print("🔒 Escrow Pattern: ENABLED")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
