import subprocess
import json
import time
import threading
from datetime import datetime
import os

class FabricGatewayClient:
    def __init__(self, peer_address="10.34.100.126:7051", orderer_address="10.34.100.121:7050"):
        self.peer_address = peer_address
        self.orderer_address = orderer_address
        self.channel_name = "ecgchannel"
        self.chaincode_name = "ecgcontract"
        
    def _execute_peer_command(self, command):
        """Execute peer CLI command dan return hasil"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout, 'error': None}
            else:
                return {'success': False, 'output': None, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': None, 'error': 'Command timeout'}
        except Exception as e:
            return {'success': False, 'output': None, 'error': str(e)}

    def store_ecg_data(self, patient_id, ipfs_hash, metadata, patient_owner_client_id):
        """Store ECG data ke blockchain - Case: Dr. Sarah menyimpan ECG Maria"""
        try:
            metadata_json = json.dumps(metadata).replace('"', '\\"')
            
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"storeECGData","Args":["{patient_id}","{ipfs_hash}","{datetime.now().isoformat()}","{metadata_json}","{patient_owner_client_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success'] and 'Chaincode invoke successful' in result['output']:
                # Start verification process in background
                self.start_verification(patient_id, ipfs_hash)
                
                return {
                    'status': 'success',
                    'message': 'ECG data stored with PENDING verification',
                    'patientID': patient_id,
                    'verificationStatus': 'PENDING_VERIFICATION'
                }
            else:
                return {'status': 'error', 'message': 'Failed to store ECG data', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'message': 'Exception occurred', 'error': str(e)}

    def grant_access(self, patient_id, doctor_client_id):
        """Grant access - Case: Maria memberikan akses ke Dr. Ahmad"""
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
                    'message': f'Access granted to specialist for second opinion',
                    'patientID': patient_id,
                    'grantedTo': doctor_client_id
                }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def revoke_access(self, patient_id, doctor_client_id):
        """Revoke access - Case: Maria mencabut akses Dr. Ahmad setelah konsultasi"""
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
                    'message': f'Access revoked after consultation completed',
                    'patientID': patient_id,
                    'revokedFrom': doctor_client_id
                }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def access_ecg_data(self, patient_id):
        """Access ECG data - Case: Dr. Ahmad mengakses data ECG Maria"""
        try:
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"accessECGData","Args":["{patient_id}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                # Parse payload untuk mendapatkan ECG data info
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

    def get_audit_trail(self, patient_id):
        """Get audit trail - Case: Transparansi semua aktivitas Maria"""
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

    def confirm_ecg_data(self, patient_id, is_valid, verification_details):
        """Confirm verification status"""
        try:
            cmd = f'''peer chaincode invoke -o {self.orderer_address} \\
                --ordererTLSHostnameOverride orderer.example.com \\
                --tls --cafile /app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \\
                -C {self.channel_name} -n {self.chaincode_name} \\
                -c '{{"function":"confirmECGData","Args":["{patient_id}","{str(is_valid).lower()}","{verification_details}"]}}' \\
                --peerAddresses {self.peer_address} --tlsRootCertFiles /app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'''
            
            result = self._execute_peer_command(cmd)
            
            if result['success']:
                return {'status': 'success', 'message': 'ECG data verification confirmed'}
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def start_verification(self, patient_id, ipfs_hash):
        """Start background verification process"""
        verification_thread = threading.Thread(
            target=self._verify_ipfs_data,
            args=(patient_id, ipfs_hash)
        )
        verification_thread.daemon = True
        verification_thread.start()
    
    def _verify_ipfs_data(self, patient_id, ipfs_hash):
        """Background IPFS verification - auto confirm after 5 seconds"""
        try:
            time.sleep(5)  # Simulate verification time
            
            # For demo, always successful verification
            is_valid = True
            details = "IPFS data verified successfully - ECG format valid"
            
            # Update status ke CONFIRMED
            result = self.confirm_ecg_data(patient_id, is_valid, details)
            print(f"✅ Verification completed for {patient_id}: {result}")
            
        except Exception as e:
            print(f"❌ Verification error for {patient_id}: {str(e)}")
            self.confirm_ecg_data(patient_id, False, f"Verification error: {str(e)}")

    def get_connection_info(self):
        """Get connection info"""
        return {
            'peerAddress': self.peer_address,
            'ordererAddress': self.orderer_address,
            'channelName': self.channel_name,
            'chaincodeName': self.chaincode_name,
            'status': 'connected',
            'timestamp': datetime.now().isoformat()
        }
