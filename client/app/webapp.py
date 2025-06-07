from flask import Flask, jsonify, request
import json
import os
import threading
import time
import logging
from datetime import datetime

from ipfsClient import IPFSClient

app = Flask(__name__)

# Initialize IPFS client  
ipfs_client = IPFSClient(ipfs_host='172.20.1.6', ipfs_port=5001)

# Enhanced Alert System for Escrow Pattern
class ECGAlertSystem:
    def __init__(self):
        self.alert_log = "/tmp/ecg_container_alerts.log"
        self.verification_log = "/tmp/ecg_container_verification.log"
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ECG_CONTAINER - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.alert_log),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ECGAlert')
        
    def alert_ecg_stored(self, patient_id, ipfs_hash, metadata):
        """Alert when ECG data stored with PENDING status"""
        message = f"🚨 ECG STORED (PENDING): Patient {patient_id}"
        details = [
            f"IPFS Hash: {ipfs_hash[:20]}...",
            f"Hospital: {metadata.get('hospital', 'Unknown')}",
            f"Doctor: {metadata.get('doctor', 'Unknown')}",
            f"Status: PENDING_VERIFICATION",
            f"⏳ Awaiting blockchain verification..."
        ]
        self.display_alert(message, details)
        
    def alert_verification_started(self, patient_id, ipfs_hash):
        """Alert when IPFS verification starts"""
        message = f"🔍 VERIFICATION STARTED: Patient {patient_id}"
        details = [
            f"IPFS Hash: {ipfs_hash[:20]}...",
            f"🔄 Checking data integrity...",
            f"📊 Validating ECG format..."
        ]
        self.display_alert(message, details)
        
    def alert_verification_completed(self, patient_id, is_valid, details):
        """Alert when verification completes"""
        status = "CONFIRMED" if is_valid else "FAILED"
        emoji = "✅" if is_valid else "❌"
        
        message = f"{emoji} VERIFICATION {status}: Patient {patient_id}"
        alert_details = [
            f"Result: {status}",
            f"Details: {details}",
            f"{'📊 Data now accessible' if is_valid else '🚫 Data blocked'}"
        ]
        self.display_alert(message, alert_details)
        
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

# Mock ECG Client untuk simulate blockchain calls
class MockECGClient:
    def __init__(self):
        self.stored_data = {}  # Simulate blockchain state
        
    def store_ecg_data(self, patient_id, ipfs_hash, metadata):
        """Simulate blockchain ECG storage with escrow"""
        # Step 1: Store with PENDING status
        self.stored_data[patient_id] = {
            'ipfsHash': ipfs_hash,
            'metadata': metadata,
            'status': 'PENDING_VERIFICATION',
            'timestamp': datetime.now().isoformat()
        }
        
        # Alert: ECG stored
        alert_system.alert_ecg_stored(patient_id, ipfs_hash, metadata)
        
        # Step 2: Start verification process
        self.start_verification(patient_id, ipfs_hash)
        
        return {
            'status': 'success',
            'message': 'ECG data stored with PENDING verification',
            'patientID': patient_id,
            'verificationStatus': 'PENDING_VERIFICATION'
        }
    
    def start_verification(self, patient_id, ipfs_hash):
        """Start IPFS verification process"""
        # Alert: Verification started
        alert_system.alert_verification_started(patient_id, ipfs_hash)
        
        # Run verification in background thread
        verification_thread = threading.Thread(
            target=self.verify_ipfs_data,
            args=(patient_id, ipfs_hash)
        )
        verification_thread.daemon = True
        verification_thread.start()
    
    def verify_ipfs_data(self, patient_id, ipfs_hash):
        """Background IPFS verification"""
        try:
            # Simulate verification delay
            time.sleep(5)
            
            # Simulate verification process (95% success rate)
            import random
            is_valid = random.random() > 0.05
            
            if is_valid:
                # Try to verify actual IPFS data
                try:
                    data = ipfs_client.get_ecg_data(ipfs_hash)
                    details = "IPFS data verified successfully"
                    
                    # Update status to CONFIRMED
                    if patient_id in self.stored_data:
                        self.stored_data[patient_id]['status'] = 'CONFIRMED'
                        self.stored_data[patient_id]['verificationDetails'] = {
                            'verifiedAt': datetime.now().isoformat(),
                            'result': 'CONFIRMED'
                        }
                        
                except Exception as e:
                    is_valid = False
                    details = f"IPFS verification failed: {str(e)}"
            else:
                details = "Simulated verification failure"
                
            if not is_valid and patient_id in self.stored_data:
                self.stored_data[patient_id]['status'] = 'FAILED'
                self.stored_data[patient_id]['verificationDetails'] = {
                    'verifiedAt': datetime.now().isoformat(),
                    'result': 'FAILED',
                    'error': details
                }
            
            # Alert: Verification completed
            alert_system.alert_verification_completed(patient_id, is_valid, details)
            
        except Exception as e:
            # Alert: Verification error
            alert_system.alert_verification_completed(patient_id, False, f"Verification error: {str(e)}")
    
    def get_ecg_status(self, patient_id):
        """Get ECG data status"""
        if patient_id in self.stored_data:
            return self.stored_data[patient_id]
        return None
    
    def access_ecg_data(self, patient_id):
        """Access ECG data (only if CONFIRMED)"""
        if patient_id not in self.stored_data:
            return {'error': 'Patient data not found'}
            
        data = self.stored_data[patient_id]
        
        if data['status'] != 'CONFIRMED':
            return {
                'error': f'Data not accessible - Status: {data["status"]}',
                'status': data['status']
            }
        
        # Access allowed - get IPFS data
        try:
            ipfs_data = ipfs_client.get_ecg_data(data['ipfsHash'])
            return {
                'status': 'success',
                'data': ipfs_data,
                'metadata': data['metadata'],
                'verificationStatus': data['status']
            }
        except Exception as e:
            return {'error': f'Failed to retrieve IPFS data: {str(e)}'}

# Initialize mock ECG client
ecg_client = MockECGClient()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check with escrow status"""
    ipfs_status = ipfs_client.get_status()
    
    return jsonify({
        "status": "UP",
        "ipfs": ipfs_status,
        "escrowPattern": "ENABLED",
        "alertSystem": "ACTIVE",
        "timestamp": datetime.now().isoformat(),
        "logs": {
            "alerts": "/tmp/ecg_container_alerts.log",
            "verification": "/tmp/ecg_container_verification.log"
        }
    })

@app.route('/ecg/upload', methods=['POST'])
def upload_ecg():
    """Upload ECG data dengan Escrow Pattern"""
    try:
        data = request.json
        patient_id = data.get('patientId')
        ecg_data = data.get('ecgData')
        metadata = data.get('metadata', {})
        
        if not patient_id or not ecg_data:
            return jsonify({"error": "Missing required fields: patientId, ecgData"}), 400
        
        # Step 1: Upload to IPFS
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)
        
        # Step 2: Store metadata dengan ESCROW pattern
        result = ecg_client.store_ecg_data(patient_id, ipfs_hash, metadata)
        
        return jsonify({
            "status": "success",
            "message": "ECG data uploaded with escrow verification",
            "patientId": patient_id,
            "ipfsHash": ipfs_hash,
            "verificationStatus": "PENDING_VERIFICATION",
            "escrowResult": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/status/<patient_id>', methods=['GET'])
def get_ecg_status(patient_id):
    """Get ECG data verification status"""
    try:
        status = ecg_client.get_ecg_status(patient_id)
        
        if not status:
            return jsonify({"error": "Patient data not found"}), 404
        
        return jsonify({
            "status": "success",
            "patientId": patient_id,
            "verificationStatus": status['status'],
            "timestamp": status['timestamp'],
            "verificationDetails": status.get('verificationDetails'),
            "accessibleForDataAccess": status['status'] == 'CONFIRMED'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg(patient_id):
    """Access ECG data (only CONFIRMED data)"""
    try:
        result = ecg_client.access_ecg_data(patient_id)
        
        if 'error' in result:
            return jsonify(result), 403 if 'not accessible' in result['error'] else 404
        
        return jsonify({
            "status": "success",
            "patientId": patient_id,
            "ecgData": result['data'],
            "metadata": result['metadata'],
            "verificationStatus": result['verificationStatus']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ecg/logs', methods=['GET'])
def get_logs():
    """Get recent alert logs"""
    try:
        logs = []
        
        # Read recent alerts
        if os.path.exists("/tmp/ecg_container_alerts.log"):
            with open("/tmp/ecg_container_alerts.log", 'r') as f:
                logs = f.readlines()[-10:]  # Last 10 lines
        
        return jsonify({
            "status": "success",
            "recentAlerts": [log.strip() for log in logs],
            "logFiles": {
                "alerts": "/tmp/ecg_container_alerts.log",
                "verification": "/tmp/ecg_container_verification.log"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting ECG Blockchain Client with Escrow Pattern...")
    print("📋 Available endpoints:")
    print("  - GET  /health")
    print("  - POST /ecg/upload") 
    print("  - GET  /ecg/status/<patient_id>")
    print("  - GET  /ecg/access/<patient_id>")
    print("  - GET  /ecg/logs")
    print("\n🔒 Escrow Pattern: ENABLED")
    print("🚨 Alert System: ACTIVE")
    print("📝 Logs: /tmp/ecg_container_alerts.log")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
