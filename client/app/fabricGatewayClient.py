import grpc
import json
import time
import logging
import os
import subprocess
import threading
from datetime import datetime

class FabricGatewayClient:
    def __init__(self, peer_address="localhost:7051", orderer_address="10.34.100.121:7050", channel_name="ecgchannel", chaincode_name="ecgcontract"):
        """
        Initialize Fabric Gateway Client menggunakan peer CLI commands
        untuk connect ke blockchain network
        """
        self.peer_address = peer_address
        self.orderer_address = orderer_address
        self.channel_name = channel_name
        self.chaincode_name = chaincode_name
        self.setup_environment()
        
    def setup_environment(self):
        """Setup environment variables untuk peer CLI"""
        os.environ['FABRIC_CFG_PATH'] = '/app/config'
        os.environ['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
        os.environ['CORE_PEER_TLS_ROOTCERT_FILE'] = '/app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'
        os.environ['CORE_PEER_MSPCONFIGPATH'] = '/app/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp'
        os.environ['CORE_PEER_ADDRESS'] = self.peer_address
        os.environ['CORE_PEER_TLS_ENABLED'] = 'true'
        
    def _execute_peer_command(self, command):
        """Execute peer CLI command dan return hasil"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout, 'error': None}
            else:
                return {'success': False, 'output': None, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': None, 'error': 'Command timeout'}
        except Exception as e:
            return {'success': False, 'output': None, 'error': str(e)}

    def store_ecg_data(self, patient_id, ipfs_hash, metadata, patient_owner_client_id):
        """Store ECG data ke blockchain menggunakan chaincode invoke"""
        try:
            metadata_json = json.dumps(metadata).replace('"', '\\"')
            
            # Construct peer chaincode invoke command
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"storeECGData","Args":["{patient_id}","{ipfs_hash}","{datetime.now().isoformat()}","{metadata_json}","{patient_owner_client_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                # Parse chaincode response
                if 'Chaincode invoke successful' in result['output']:
                    # Extract payload from peer response
                    lines = result['output'].split('\n')
                    for line in lines:
                        if 'payload:' in line:
                            payload_str = line.split('payload:')[1].strip()
                            try:
                                payload_data = json.loads(payload_str)
                                return {
                                    'status': 'success',
                                    'message': 'ECG data stored with PENDING verification',
                                    'patientID': patient_id,
                                    'verificationStatus': 'PENDING_VERIFICATION',
                                    'blockchainResponse': payload_data
                                }
                            except json.JSONDecodeError:
                                return {
                                    'status': 'success',
                                    'message': 'ECG data stored successfully',
                                    'patientID': patient_id,
                                    'rawResponse': payload_str
                                }
                
                return {
                    'status': 'success',
                    'message': 'ECG data stored successfully',
                    'patientID': patient_id,
                    'output': result['output']
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to store ECG data',
                    'error': result['error']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': 'Exception occurred during store operation',
                'error': str(e)
            }

    def confirm_ecg_data(self, patient_id, is_valid, verification_details):
        """Confirm ECG data verification status"""
        try:
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"confirmECGData","Args":["{patient_id}","{str(is_valid).lower()}","{verification_details}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                return {'status': 'success', 'message': 'ECG data verification updated'}
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def grant_access(self, patient_id, doctor_client_id):
        """Grant access to ECG data for specific doctor"""
        try:
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"grantAccess","Args":["{patient_id}","{doctor_client_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                return {
                    'status': 'success', 
                    'message': f'Access granted to {doctor_client_id} for patient {patient_id}',
                    'patientID': patient_id,
                    'grantedTo': doctor_client_id
                }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def revoke_access(self, patient_id, doctor_client_id):
        """Revoke access from ECG data for specific doctor"""
        try:
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"revokeAccess","Args":["{patient_id}","{doctor_client_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                return {
                    'status': 'success', 
                    'message': f'Access revoked from {doctor_client_id} for patient {patient_id}',
                    'patientID': patient_id,
                    'revokedFrom': doctor_client_id
                }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def access_ecg_data(self, patient_id):
        """Access ECG data (only if CONFIRMED and authorized)"""
        try:
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"accessECGData","Args":["{patient_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                # Parse payload to get ECG data info
                lines = result['output'].split('\n')
                for line in lines:
                    if 'payload:' in line:
                        payload_str = line.split('payload:')[1].strip()
                        try:
                            ecg_info = json.loads(payload_str)
                            return {
                                'status': 'success',
                                'patientID': patient_id,
                                'ecgInfo': ecg_info,
                                'accessGranted': True
                            }
                        except json.JSONDecodeError:
                            return {
                                'status': 'success',
                                'patientID': patient_id,
                                'rawResponse': payload_str
                            }
                
                return {'status': 'success', 'message': 'ECG data accessed successfully'}
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_ecg_status(self, patient_id):
        """Get ECG data verification status"""
        try:
            cmd = f'''peer chaincode query \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"getECGDataStatus","Args":["{patient_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                try:
                    status_data = json.loads(result['output'].strip())
                    return {
                        'status': 'success',
                        'patientId': patient_id,
                        'statusData': status_data
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'success',
                        'patientId': patient_id,
                        'rawResponse': result['output']
                    }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_audit_trail(self, patient_id):
        """Get audit trail for patient's ECG data (owner only)"""
        try:
            cmd = f'''peer chaincode query \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"getAuditTrail","Args":["{patient_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                try:
                    audit_data = json.loads(result['output'].strip())
                    return {
                        'status': 'success',
                        'patientId': patient_id,
                        'auditTrail': audit_data
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'success',
                        'patientId': patient_id,
                        'rawResponse': result['output']
                    }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_connection_info(self):
        """Get connection information for debugging"""
        return {
            'peerAddress': self.peer_address,
            'ordererAddress': self.orderer_address,
            'channelName': self.channel_name,
            'chaincodeName': self.chaincode_name,
            'status': 'connected',
            'timestamp': datetime.now().isoformat()
        }

    def start_verification(self, patient_id, ipfs_hash):
        """Start IPFS verification process in background"""
        verification_thread = threading.Thread(
            target=self._verify_ipfs_data,
            args=(patient_id, ipfs_hash)
        )
        verification_thread.daemon = True
        verification_thread.start()
    
    def _verify_ipfs_data(self, patient_id, ipfs_hash):
        """Background IPFS verification process"""
        try:
            # Simulate verification delay
            time.sleep(5)
            
            # For demo purposes, assume 95% success rate
            import random
            is_valid = random.random() > 0.05
            
            details = "IPFS data verified successfully" if is_valid else "IPFS verification failed"
            
            # Update verification status on blockchain
            result = self.confirm_ecg_data(patient_id, is_valid, details)
            print(f"Verification completed for {patient_id}: {result}")
            
        except Exception as e:
            print(f"Verification error for {patient_id}: {str(e)}")
            self.confirm_ecg_data(patient_id, False, f"Verification error: {str(e)}")

    def revoke_access(self, patient_id, doctor_id):
        """Revoke access via real blockchain"""
        print(f"🔒 Revoking access for patient {patient_id} from {doctor_id}")
        
        result = self._invoke_chaincode("revokeAccess", [patient_id, doctor_id])
        return result
    
    def get_audit_trail(self, patient_id):
        """Get audit trail via real blockchain"""
        print(f"📋 Getting audit trail for patient {patient_id}")
        
        result = self._invoke_chaincode("getAuditTrail", [patient_id])
        return result
    
    def get_ecg_status(self, patient_id):
        """Get ECG status via real blockchain"""
        print(f"ℹ️ Getting ECG status for patient {patient_id}")
        
        result = self._invoke_chaincode("getECGDataStatus", [patient_id])
        return result
    
    def confirm_ecg_data(self, patient_id, is_valid, verification_details):
        """Confirm ECG data verification via real blockchain"""
        print(f"✅ Confirming ECG verification for patient {patient_id}: {is_valid}")
        
        result = self._invoke_chaincode("confirmECGData", [patient_id, str(is_valid), verification_details])
        return result
