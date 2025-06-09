from flask import Flask, jsonify, request
import json
import os
import threading
import time
import logging
from datetime import datetime

from ipfsClient import IPFSClient
from fabricGatewayClient import FabricGatewayClient

app = Flask(__name__)

# Initialize IPFS client  
ipfs_client = IPFSClient(ipfs_host='172.20.1.6', ipfs_port=5001)

# Initialize REAL Fabric Gateway client
fabric_client = FabricGatewayClient(peer_address="10.34.100.126:7051")

# Enhanced Alert System for Escrow Pattern
class ECGAlertSystem:
    def __init__(self):
        self.alert_log = "/tmp/ecg_fabric_alerts.log"
        self.verification_log = "/tmp/ecg_fabric_verification.log"
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ECG_FABRIC - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.alert_log),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ECGFabricAlert')
        
    def alert_ecg_stored(self, patient_id, ipfs_hash, blockchain_result):
        """Alert when ECG data stored to REAL blockchain"""
        message = f"🚨 ECG STORED TO BLOCKCHAIN: Patient {patient_id}"
        details = [
            f"IPFS Hash: {ipfs_hash[:20]}...",
            f"Blockchain TxID: {blockchain_result.get('txId', 'N/A')}",
            f"Status: {blockchain_result.get('verificationStatus', 'UNKNOWN')}",
            f"Connection: {blockchain_result.get('blockchain', 'UNKNOWN')}",
            f"⛓️ Data stored in Hyperledger Fabric ledger"
        ]
        self.display_alert(message, details)
        
    def display_alert(self, message, details):
        """Display formatted alert in container logs"""
        separator = "=" * 60
        print(f"\n{separator}")
        print(f"{message}")
        print(f"{separator}")
        for detail in details:
            print(f"  {detail}")
        print(f"  🕒 Timestamp: {datetime.now().isoformat()}")
        print(f"{separator}\n")
        
        # Log to file for persistence
        log_entry = f"{message} - {' | '.join(details)}"
        self.logger.info(log_entry)

# Initialize alert system
alert_system = ECGAlertSystem()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check with REAL Fabric connection status"""
    ipfs_status = ipfs_client.get_status()
    fabric_info = fabric_client.get_connection_info()
    
    return jsonify({
        "status": "UP",
        "ipfs": ipfs_status,
        "blockchain": fabric_info,
        "escrowPattern": "ENABLED",
        "alertSystem": "ACTIVE_FABRIC",
        "mockData": "DISABLED",
        "timestamp": datetime.now().isoformat(),
        "logs": {
            "alerts": "/tmp/ecg_fabric_alerts.log",
            "verification": "/tmp/ecg_fabric_verification.log"
        }
    })

@app.route('/ecg/upload', methods=['POST'])
def upload_ecg():
    """Upload ECG data to REAL blockchain dengan Escrow Pattern"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        ecg_data = data.get('ecgData')
        metadata = data.get('metadata', {})
        patient_owner_id = data.get('patientOwnerClientID', f'x509::CN={patient_id}')
        
        if not patient_id or not ecg_data:
            return jsonify({"error": "Missing required fields: patientId, ecgData"}), 400
        
        # Step 1: Upload to IPFS
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)
        
        # Step 2: Store metadata to REAL blockchain via Fabric Gateway
        blockchain_result = fabric_client.store_ecg_data(
            patient_id, 
            ipfs_hash, 
            metadata, 
            patient_owner_id
        )
        
        # Step 3: Alert with REAL blockchain result
        alert_system.alert_ecg_stored(patient_id, ipfs_hash, blockchain_result)
        
        return jsonify({
            "status": "success",
            "message": "ECG data uploaded to REAL blockchain with escrow verification",
            "patientId": patient_id,
            "ipfsHash": ipfs_hash,
            "blockchainResult": blockchain_result,
            "verificationStatus": blockchain_result.get("verificationStatus", "PENDING"),
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg(patient_id):
    """Access ECG data from REAL blockchain"""
    try:
        # Access via REAL Fabric Gateway
        result = fabric_client.access_ecg_data(patient_id)
        
        if 'error' in result:
            return jsonify(result), 403 if 'not accessible' in result['error'] else 404
        
        return jsonify({
            "status": "success",
            "patientId": patient_id,
            "blockchainData": result,
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/grant-access', methods=['POST'])
def grant_access():
    """Grant access via REAL blockchain"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID')
        
        if not patient_id or not doctor_id:
            return jsonify({"error": "Missing patientId or doctorClientID"}), 400
        
        # Grant via REAL Fabric Gateway
        result = fabric_client.grant_access(patient_id, doctor_id)
        
        return jsonify({
            "status": "success",
            "message": "Access granted via REAL blockchain",
            "blockchainResult": result,
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/logs', methods=['GET'])
def get_logs():
    """Get recent REAL blockchain logs"""
    try:
        logs = []
        
        # Read recent alerts
        if os.path.exists("/tmp/ecg_fabric_alerts.log"):
            with open("/tmp/ecg_fabric_alerts.log", 'r') as f:
                logs = f.readlines()[-10:]  # Last 10 lines
        
        return jsonify({
            "status": "success",
            "recentAlerts": [log.strip() for log in logs],
            "logFiles": {
                "alerts": "/tmp/ecg_fabric_alerts.log",
                "verification": "/tmp/ecg_fabric_verification.log"
            },
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting ECG Blockchain Client with REAL Fabric Gateway...")
    print("📋 Available endpoints:")
    print("  - GET  /health")
    print("  - POST /ecg/upload") 
    print("  - GET  /ecg/access/<patient_id>")
    print("  - POST /ecg/grant-access")
    print("  - POST /ecg/revoke-access")
    print("  - GET  /ecg/audit/<patient_id>")
    print("  - GET  /ecg/status/<patient_id>")
    print("  - POST /ecg/confirm")
    print("  - GET  /ecg/logs")
    print("\n⛓️  Blockchain: REAL HYPERLEDGER FABRIC")
    print("🔒 Escrow Pattern: ENABLED")
    print("🚨 Alert System: ACTIVE")
    print("📝 Logs: /tmp/ecg_fabric_alerts.log")
    
    app.run(host='0.0.0.0', port=3000, debug=True)

@app.route('/ecg/revoke-access', methods=['POST'])
def revoke_access():
    """Revoke access via REAL blockchain"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID')
        
        if not patient_id or not doctor_id:
            return jsonify({"error": "Missing patientId or doctorClientID"}), 400
        
        # Revoke via REAL Fabric Gateway
        result = fabric_client.revoke_access(patient_id, doctor_id)
        
        return jsonify({
            "status": "success",
            "message": "Access revoked via REAL blockchain",
            "blockchainResult": result,
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/audit/<patient_id>', methods=['GET'])
def get_audit_trail(patient_id):
    """Get audit trail from REAL blockchain"""
    try:
        # Get audit via REAL Fabric Gateway
        result = fabric_client.get_audit_trail(patient_id)
        
        return jsonify({
            "status": "success",
            "patientId": patient_id,
            "auditTrail": result,
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/status/<patient_id>', methods=['GET'])
def get_ecg_status(patient_id):
    """Get ECG data status from REAL blockchain"""
    try:
        # Get status via REAL Fabric Gateway
        result = fabric_client.get_ecg_status(patient_id)
        
        return jsonify({
            "status": "success",
            "patientId": patient_id,
            "ecgStatus": result,
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/confirm', methods=['POST'])
def confirm_ecg_verification():
    """Confirm ECG data verification (for escrow pattern)"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        is_valid = data.get('isValid', True)
        verification_details = data.get('verificationDetails', 'Manual confirmation')
        
        if not patient_id:
            return jsonify({"error": "Missing patientId"}), 400
        
        # Confirm via REAL Fabric Gateway
        result = fabric_client.confirm_ecg_data(patient_id, is_valid, verification_details)
        
        return jsonify({
            "status": "success",
            "message": "ECG verification confirmed via REAL blockchain",
            "blockchainResult": result,
            "mockData": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
