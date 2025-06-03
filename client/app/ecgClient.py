import grpc
import json
import datetime
from typing import Dict, Any, List
import time

class ECGClient:
    def __init__(self, gateway_endpoint="10.34.100.126:7051", channel_name="ecgchannel", chaincode_name="ecgcc"):
        """
        Initialize ECG client with Fabric Gateway
        
        Args:
            gateway_endpoint: Peer endpoint to connect as gateway
            channel_name: Channel name
            chaincode_name: Chaincode name
        """
        self.gateway_endpoint = gateway_endpoint
        self.channel_name = channel_name
        self.chaincode_name = chaincode_name
        
    def _create_mock_transaction(self, function_name: str, args: List[str]) -> Dict[str, Any]:
        """
        Create mock transaction for testing
        In production, this would use actual Fabric Gateway gRPC calls
        """
        transaction_id = f"txn_{int(time.time())}"
        
        return {
            "status": "success",
            "transactionId": transaction_id,
            "function": function_name,
            "args": args,
            "timestamp": datetime.datetime.now().isoformat(),
            "endorsements": ["peer0.org1.example.com", "peer0.org2.example.com"],
            "blockNumber": 1,
            "gatewayEndpoint": self.gateway_endpoint
        }
    
    def store_ecg_data(self, patient_id: str, ipfs_hash: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Store ECG data metadata on blockchain via Gateway
        
        Args:
            patient_id: Patient identifier
            ipfs_hash: IPFS hash of ECG data
            metadata: Additional metadata
            
        Returns:
            Transaction response
        """
        timestamp = datetime.datetime.now().isoformat()
        metadata_str = json.dumps(metadata) if metadata else '{}'
        
        # Mock Gateway transaction
        response = self._create_mock_transaction(
            "storeECGData",
            [patient_id, ipfs_hash, timestamp, metadata_str]
        )
        
        # Add ECG-specific response data
        response.update({
            "patientId": patient_id,
            "ipfsHash": ipfs_hash,
            "stored": True
        })
        
        return response
    
    def grant_access(self, patient_id: str, user_id: str) -> Dict[str, Any]:
        """Grant access to ECG data"""
        response = self._create_mock_transaction("grantAccess", [patient_id, user_id])
        response.update({
            "patientId": patient_id,
            "grantedTo": user_id,
            "accessGranted": True
        })
        return response
    
    def revoke_access(self, patient_id: str, user_id: str) -> Dict[str, Any]:
        """Revoke access from ECG data"""
        response = self._create_mock_transaction("revokeAccess", [patient_id, user_id])
        response.update({
            "patientId": patient_id,
            "revokedFrom": user_id,
            "accessRevoked": True
        })
        return response
    
    def access_ecg_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Access ECG data and record in audit trail
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            ECG data information with IPFS hash
        """
        # Mock query transaction
        response = self._create_mock_transaction("accessECGData", [patient_id])
        
        # Mock ECG data response
        response.update({
            "patientId": patient_id,
            "ipfsHash": f"QmX{patient_id}MockHash123",
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": {
                "hospital": "General Hospital",
                "device": "ECG-DEVICE-001",
                "heartRate": 72
            },
            "accessRecorded": True
        })
        
        return response
    
    def get_audit_trail(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get audit trail for patient's ECG data
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            List of audit records
        """
        # Mock audit trail
        audit_trail = [
            {
                "accessorId": "DR001",
                "timestamp": "2025-06-02T10:30:00Z",
                "action": "access",
                "ipAddress": "10.34.100.125"
            },
            {
                "accessorId": "NURSE002", 
                "timestamp": "2025-06-02T11:15:00Z",
                "action": "access",
                "ipAddress": "10.34.100.114"
            }
        ]
        
        return audit_trail
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging"""
        return {
            "gatewayEndpoint": self.gateway_endpoint,
            "channelName": self.channel_name,
            "chaincodeName": self.chaincode_name,
            "status": "connected",
            "timestamp": datetime.datetime.now().isoformat()
        }
