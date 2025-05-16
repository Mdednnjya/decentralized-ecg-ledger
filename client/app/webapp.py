from flask import Flask, jsonify, request
import asyncio
import json
import os

from ipfsClient import IPFSClient
from ecgClient import ECGClient

app = Flask(__name__)

# Initialize clients
ipfs_client = IPFSClient(ipfs_host='10.34.1.5', ipfs_port=5001)
ecg_client = ECGClient(
    channel_name='ecgchannel',
    org_name='Org1',
    user_name='User1',
    config_path='../config/connection-org1.json'
)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "UP"})


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
            return jsonify({"error": "Missing required fields"}), 400

        # Upload to IPFS
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)

        # Store on blockchain
        result = asyncio.run(ecg_client.store_ecg_data(patient_id, ipfs_hash, metadata))

        return jsonify({
            "status": "success",
            "ipfsHash": ipfs_hash,
            "blockchainResponse": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg(patient_id):
    """Access ECG data for a patient"""
    try:
        # Get ECG metadata from blockchain
        blockchain_result = asyncio.run(ecg_client.access_ecg_data(patient_id))

        # Get actual ECG data from IPFS
        ipfs_hash = blockchain_result.get('ipfsHash')
        ecg_data = ipfs_client.get_ecg_data(ipfs_hash)

        return jsonify({
            "status": "success",
            "metadata": blockchain_result,
            "ecgData": ecg_data
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
            return jsonify({"error": "Missing required fields"}), 400

        # Grant access
        result = asyncio.run(ecg_client.grant_access(patient_id, user_id))

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
            return jsonify({"error": "Missing required fields"}), 400

        # Revoke access
        result = asyncio.run(ecg_client.revoke_access(patient_id, user_id))

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
        # Get audit trail
        result = asyncio.run(ecg_client.get_audit_trail(patient_id))

        return jsonify({
            "status": "success",
            "auditTrail": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)