import asyncio
import json
import logging
from datetime import datetime
import time
import os

# Simple console-based alert service
class ECGAlertService:
    def __init__(self):
        self.alert_log_file = "/tmp/ecg_alerts.log"
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.alert_log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def process_ecg_data_stored_event(self, event_data):
        """Process ECG data stored event"""
        patient_id = event_data.get('patientID', 'Unknown')
        hospital = event_data.get('hospital', 'Unknown Hospital')
        doctor = event_data.get('doctor', 'Unknown Doctor')
        timestamp = event_data.get('timestamp', '')
        
        alert_message = f"🚨 NEW ECG DATA ALERT 🚨"
        alert_details = [
            f"Patient ID: {patient_id}",
            f"Hospital: {hospital}",
            f"Doctor: {doctor}",
            f"Timestamp: {timestamp}",
            f"IPFS Hash: {event_data.get('ipfsHash', 'N/A')[:20]}..."
        ]
        
        self.display_alert(alert_message, alert_details)
        
    def process_access_granted_event(self, event_data):
        """Process access granted event"""
        patient_id = event_data.get('patientID', 'Unknown')
        granted_to = event_data.get('grantedTo', 'Unknown Doctor')
        timestamp = event_data.get('timestamp', '')
        
        alert_message = f"🔓 ACCESS GRANTED ALERT"
        alert_details = [
            f"Patient ID: {patient_id}",
            f"Access granted to: {granted_to.split('CN=')[-1].split('::')[0] if 'CN=' in granted_to else granted_to}",
            f"Timestamp: {timestamp}"
        ]
        
        self.display_alert(alert_message, alert_details)
        
    def process_access_revoked_event(self, event_data):
        """Process access revoked event"""
        patient_id = event_data.get('patientID', 'Unknown')
        revoked_from = event_data.get('revokedFrom', 'Unknown Doctor')
        timestamp = event_data.get('timestamp', '')
        
        alert_message = f"🔒 ACCESS REVOKED ALERT"
        alert_details = [
            f"Patient ID: {patient_id}",
            f"Access revoked from: {revoked_from.split('CN=')[-1].split('::')[0] if 'CN=' in revoked_from else revoked_from}",
            f"Timestamp: {timestamp}"
        ]
        
        self.display_alert(alert_message, alert_details)
        
    def process_ecg_data_accessed_event(self, event_data):
        """Process ECG data accessed event"""
        patient_id = event_data.get('patientID', 'Unknown')
        accessed_by = event_data.get('accessedBy', 'Unknown')
        timestamp = event_data.get('timestamp', '')
        
        alert_message = f"📋 DATA ACCESS ALERT"
        alert_details = [
            f"Patient ID: {patient_id}",
            f"Accessed by: {accessed_by.split('CN=')[-1].split('::')[0] if 'CN=' in accessed_by else accessed_by}",
            f"Timestamp: {timestamp}"
        ]
        
        self.display_alert(alert_message, alert_details)
        
    def display_alert(self, message, details):
        """Display alert in console and log to file"""
        separator = "=" * 60
        
        # Console output dengan formatting
        print(f"\n{separator}")
        print(f"{message}")
        print(f"{separator}")
        for detail in details:
            print(f"  {detail}")
        print(f"{separator}\n")
        
        # Log to file
        log_entry = f"{message} - {' | '.join(details)}"
        self.logger.info(log_entry)
        
    def simulate_blockchain_events(self):
        """Simulate blockchain event listening (for testing)"""
        print("🔄 ECG Alert Service started - Listening for blockchain events...")
        print(f"📝 Alerts will be logged to: {self.alert_log_file}")
        print("📡 Monitoring for: ECG Data Storage, Access Grants/Revokes, Data Access")
        print("\n" + "="*60)
        
        # Simulate some events for testing
        sample_events = [
            {
                'eventType': 'ECG_DATA_STORED',
                'patientID': 'PAT001',
                'hospital': 'RS Jakarta Pusat',
                'doctor': 'DR001',
                'timestamp': datetime.now().isoformat(),
                'ipfsHash': 'QmTestHash123456789'
            },
            {
                'eventType': 'ACCESS_GRANTED', 
                'patientID': 'PAT001',
                'grantedTo': 'x509::/CN=DrSmith@org2.example.com',
                'timestamp': datetime.now().isoformat()
            },
            {
                'eventType': 'ECG_DATA_ACCESSED',
                'patientID': 'PAT001', 
                'accessedBy': 'x509::/CN=DrSmith@org2.example.com',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        for i, event in enumerate(sample_events):
            time.sleep(2)  # Simulate delay between events
            self.process_event(event)
            
    def process_event(self, event_data):
        """Process incoming blockchain event"""
        event_type = event_data.get('eventType', '')
        
        if event_type == 'ECG_DATA_STORED':
            self.process_ecg_data_stored_event(event_data)
        elif event_type == 'ACCESS_GRANTED':
            self.process_access_granted_event(event_data)
        elif event_type == 'ACCESS_REVOKED':
            self.process_access_revoked_event(event_data)
        elif event_type == 'ECG_DATA_ACCESSED':
            self.process_ecg_data_accessed_event(event_data)
        else:
            self.logger.warning(f"Unknown event type: {event_type}")

if __name__ == "__main__":
    alert_service = ECGAlertService()
    
    try:
        # In production, this would connect to Fabric Gateway and listen to actual events
        # For now, simulate the service
        alert_service.simulate_blockchain_events()
        
        # Keep service running
        print("\n🔄 Service running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 ECG Alert Service stopped by user")
    except Exception as e:
        print(f"\n❌ Error in alert service: {e}")
