import ipfshttpclient
import json
import os

class IPFSClient:
    def __init__(self, ipfs_host='172.20.1.6', ipfs_port=5001):
        """
        Initialize IPFS client
        
        Args:
            ipfs_host: IPFS container IP in Docker network
            ipfs_port: IPFS port
        """
        try:
            self.client = ipfshttpclient.connect(f'/ip4/{ipfs_host}/tcp/{ipfs_port}')
            # Test connection
            version = self.client.version()
            print(f"✓ Connected to IPFS version: {version['Version']} at {ipfs_host}:{ipfs_port}")
        except Exception as e:
            print(f"⚠️ IPFS connection failed to {ipfs_host}:{ipfs_port} - {e}")
            self.client = None

    def upload_ecg_data(self, ecg_data):
        """
        Upload ECG data to IPFS

        Args:
            ecg_data (dict): ECG data in JSON format

        Returns:
            str: IPFS hash of the uploaded data
        """
        if not self.client:
            # Return mock hash if IPFS not available
            mock_hash = f"QmMockHash{abs(hash(str(ecg_data)))}"[:46]
            print(f"📝 Using mock IPFS hash: {mock_hash}")
            return mock_hash
        
        try:
            # Convert ECG data to JSON string
            ecg_json = json.dumps(ecg_data, indent=2)

            # Add data to IPFS
            res = self.client.add_str(ecg_json)
            print(f"✓ ECG data uploaded to IPFS: {res}")
            return res
        except Exception as e:
            print(f"⚠️ IPFS upload failed: {e}")
            # Return mock hash as fallback
            mock_hash = f"QmMockHash{abs(hash(str(ecg_data)))}"[:46]
            print(f"📝 Using mock IPFS hash: {mock_hash}")
            return mock_hash

    def get_ecg_data(self, ipfs_hash):
        """
        Retrieve ECG data from IPFS

        Args:
            ipfs_hash (str): IPFS hash of the ECG data

        Returns:
            dict: ECG data as a dictionary
        """
        if not self.client:
            # Return mock data if IPFS not available
            return {
                "patientInfo": {"id": "MOCK_PATIENT", "note": "IPFS not available - using mock data"},
                "leads": {"I": [0.1, 0.2, 0.3], "II": [0.2, 0.3, 0.4]},
                "analysis": {"heartRate": 75, "rhythm": "Normal"},
                "mockData": True,
                "ipfsHash": ipfs_hash
            }
        
        try:
            # Get data from IPFS
            data = self.client.cat(ipfs_hash).decode('utf-8')

            # Parse JSON data
            ecg_data = json.loads(data)
            print(f"✓ ECG data retrieved from IPFS: {ipfs_hash}")
            return ecg_data
        except Exception as e:
            print(f"⚠️ IPFS retrieval failed for {ipfs_hash}: {e}")
            # Return mock data as fallback
            return {
                "patientInfo": {"id": "MOCK_PATIENT", "note": f"IPFS retrieval failed: {e}"},
                "leads": {"I": [0.1, 0.2, 0.3], "II": [0.2, 0.3, 0.4]},
                "analysis": {"heartRate": 75, "rhythm": "Normal"},
                "mockData": True,
                "ipfsHash": ipfs_hash,
                "error": str(e)
            }
    
    def get_status(self):
        """Get IPFS connection status"""
        if not self.client:
            return {
                "status": "disconnected", 
                "error": "No IPFS connection",
                "fallback": "Using mock data"
            }
        
        try:
            version = self.client.version()
            return {
                "status": "connected",
                "version": version['Version'],
                "api": "172.20.1.6:5001",
                "peer_id": version.get('PeerID', 'unknown')
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "fallback": "Using mock data"
            }
