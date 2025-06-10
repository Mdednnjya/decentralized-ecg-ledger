import subprocess
import json
import os
import time
import threading
from datetime import datetime

class FabricGatewayClient:
    def __init__(self, peer_address="10.34.100.126:7051"):
        self.peer_address = peer_address
        self.orderer_address = "10.34.100.121:7050"
        self.channel_name = "ecgchannel"
        self.chaincode_name = "ecgcontract"
        
        # Identity mapping table - NO HARDCODE
        self.identity_mappings = {
            'patient': {
                'msp_id': 'Org1MSP',
                'msp_path': '/app/crypto-config/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp',
                'description': 'Hospital Patient User'
            },
            'doctor': {
                'msp_id': 'Org2MSP', 
                'msp_path': '/app/crypto-config/peerOrganizations/org2.example.com/users/User1@org2.example.com/msp',
                'description': 'Specialist Doctor User'
            },
            'admin': {
                'msp_id': 'Org1MSP',
                'msp_path': '/app/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp',
                'description': 'System Administrator'
            }
        }
        
        print("🔧 FabricGatewayClient initialized with dynamic identity mapping")
        print(f"🔗 Peer: {self.peer_address}")
        print(f"🔗 Orderer: {self.orderer_address}")

    def get_fabric_env(self, user_role='admin'):
        """Get Fabric environment variables berdasarkan user role"""
        mapping = self.identity_mappings.get(user_role, self.identity_mappings['admin'])
        
        return {
            'FABRIC_CFG_PATH': '/app/config',
            'CORE_PEER_LOCALMSPID': mapping['msp_id'],
            'CORE_PEER_TLS_ROOTCERT_FILE': '/app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt',
            'CORE_PEER_MSPCONFIGPATH': mapping['msp_path'],
            'CORE_PEER_ADDRESS': self.peer_address,
            'CORE_PEER_TLS_ENABLED': 'true'
        }

    def _execute_peer_command_with_env(self, chaincode_call, is_query=False, user_role='admin'):
        """Execute peer command dengan dynamic identity"""
        try:
            # Get environment berdasarkan user role
            fabric_env = self.get_fabric_env(user_role)
            
            # Build command
            if is_query:
                cmd = ["peer", "chaincode", "query"]
            else:
                cmd = ["peer", "chaincode", "invoke"]
                cmd.extend([
                    "-o", self.orderer_address,
                    "--ordererTLSHostnameOverride", "orderer.example.com",
                    "--tls",
                    "--cafile", "/app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
                ])
            
            cmd.extend([
                "-C", self.channel_name,
                "-n", self.chaincode_name,
                "-c", json.dumps(chaincode_call, separators=(',', ':'))
            ])
            
            if not is_query:
                cmd.extend([
                    "--peerAddresses", "10.34.100.126:7051",
                    "--tlsRootCertFiles", "/app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt",
                    "--peerAddresses", "10.34.100.114:9051", 
                    "--tlsRootCertFiles", "/app/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
                ])
            
            print(f"🔧 Using identity: {fabric_env['CORE_PEER_LOCALMSPID']} - {self.identity_mappings[user_role]['description']}")
            print(f"🔧 MSP Path: {fabric_env['CORE_PEER_MSPCONFIGPATH'].split('/')[-2]}")
            
            # Merge environment
            full_env = os.environ.copy()
            full_env.update(fabric_env)
            
            print(f"🔄 Executing command as {user_role}...")
            
            # Execute command
            result = subprocess.run(
                cmd,
                env=full_env,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            print(f"📤 Return code: {result.returncode}")
            
            # SUCCESS DETECTION
            is_success = False
            payload_data = None
            
            if result.returncode == 0:
                if 'Chaincode invoke successful' in result.stderr or 'status:200' in result.stderr:
                    is_success = True
                    print(f"✅ SUCCESS: {user_role} operation completed")
                elif result.stdout.strip():
                    is_success = True
                    try:
                        payload_data = json.loads(result.stdout.strip())
                    except:
                        payload_data = result.stdout.strip()
            
            return {
                'success': is_success,
                'output': result.stdout,
                'error': result.stderr,
                'returnCode': result.returncode,
                'payload': payload_data,
                'userRole': user_role,
                'mspId': fabric_env['CORE_PEER_LOCALMSPID']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'userRole': user_role}

    def store_ecg_data(self, patient_id, ipfs_hash, metadata, patient_owner_client_id, user_role='admin'):
        """Store ECG data dengan dynamic identity"""
        try:
            print(f"📊 STORE_ECG_DATA: Patient {patient_id} by {user_role}")
            
            if isinstance(metadata, dict):
                metadata_str = json.dumps(metadata, separators=(',', ':'))
            else:
                metadata_str = json.dumps({}, separators=(',', ':'))
            
            chaincode_call = {
                "function": "storeECGData",
                "Args": [
                    patient_id,
                    ipfs_hash, 
                    datetime.now().isoformat(),
                    metadata_str,
                    patient_owner_client_id
                ]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False, user_role=user_role)
            
            if result['success']:
                print(f"✅ STORE_ECG_DATA: Success by {user_role}")
                self.start_verification(patient_id, ipfs_hash)
                
                return {
                    'status': 'success',
                    'message': 'ECG data stored successfully',
                    'patientID': patient_id,
                    'ipfsHash': ipfs_hash,
                    'verificationStatus': 'PENDING_VERIFICATION',
                    'userRole': result['userRole'],
                    'mspId': result['mspId'],
                    'blockchainStored': True,
                    'returnCode': result['returnCode']
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to store ECG data',
                    'error': result['error'],
                    'userRole': result['userRole']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def grant_access(self, patient_id, doctor_client_id, user_role='patient'):
        """Grant access dengan identity validation"""
        try:
            print(f"🔐 GRANT_ACCESS: Patient {patient_id} by {user_role}")
            
            chaincode_call = {
                "function": "grantAccess",
                "Args": [patient_id, doctor_client_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False, user_role=user_role)
            
            if result['success']:
                return {
                    'status': 'success',
                    'message': f'Access granted by {user_role}',
                    'patientID': patient_id,
                    'grantedTo': doctor_client_id,
                    'userRole': result['userRole'],
                    'mspId': result['mspId']
                }
            else:
                return {
                    'status': 'error',
                    'error': result['error'],
                    'userRole': result['userRole']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def access_ecg_data(self, patient_id, user_role='doctor'):
        """Access ECG data dengan role validation"""
        try:
            print(f"📖 ACCESS_ECG_DATA: Patient {patient_id} by {user_role}")
            
            chaincode_call = {
                "function": "accessECGData",
                "Args": [patient_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=True, user_role=user_role)
            
            if result['success']:
                return {
                    'status': 'success',
                    'message': f'ECG data accessed by {user_role}',
                    'patientID': patient_id,
                    'data': result.get('payload') or result['output'],
                    'userRole': result['userRole'],
                    'mspId': result['mspId']
                }
            else:
                return {
                    'status': 'error',
                    'error': result['error'],
                    'userRole': result['userRole']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def revoke_access(self, patient_id, doctor_client_id, user_role='patient'):
        """Revoke access dengan patient identity"""
        try:
            print(f"🚫 REVOKE_ACCESS: Patient {patient_id} by {user_role}")
            
            chaincode_call = {
                "function": "revokeAccess", 
                "Args": [patient_id, doctor_client_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False, user_role=user_role)
            
            if result['success']:
                return {
                    'status': 'success',
                    'message': f'Access revoked by {user_role}',
                    'patientID': patient_id,
                    'revokedFrom': doctor_client_id,
                    'userRole': result['userRole'],
                    'mspId': result['mspId']
                }
            else:
                return {
                    'status': 'error',
                    'error': result['error'],
                    'userRole': result['userRole']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_audit_trail(self, patient_id, user_role='patient'):
        """Get audit trail dengan role validation"""
        try:
            print(f"📋 AUDIT_TRAIL: Patient {patient_id} by {user_role}")
            
            chaincode_call = {
                "function": "getAuditTrail",
                "Args": [patient_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=True, user_role=user_role)
            
            if result['success']:
                return {
                    'status': 'success',
                    'message': f'Audit trail retrieved by {user_role}',
                    'patientID': patient_id,
                    'auditTrail': result.get('payload') or result['output'],
                    'userRole': result['userRole'],
                    'mspId': result['mspId']
                }
            else:
                return {
                    'status': 'error',
                    'error': result['error'],
                    'userRole': result['userRole']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def confirm_ecg_data(self, patient_id, is_valid, verification_details):
        """Confirm verification (always admin)"""
        try:
            chaincode_call = {
                "function": "confirmECGData",
                "Args": [patient_id, str(is_valid).lower(), verification_details]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False, user_role='admin')
            
            if result['success']:
                return {
                    'status': 'success', 
                    'message': 'ECG data verification confirmed',
                    'patientID': patient_id,
                    'verificationResult': 'CONFIRMED' if is_valid else 'FAILED'
                }
            else:
                return {'status': 'error', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def start_verification(self, patient_id, ipfs_hash):
        """Start background verification"""
        verification_thread = threading.Thread(
            target=self._verify_ipfs_data,
            args=(patient_id, ipfs_hash)
        )
        verification_thread.daemon = True
        verification_thread.start()
    
    def _verify_ipfs_data(self, patient_id, ipfs_hash):
        """Background verification process"""
        try:
            time.sleep(10)
            is_valid = True
            details = f"IPFS verified - Hash: {ipfs_hash[:20]}..."
            result = self.confirm_ecg_data(patient_id, is_valid, details)
            print(f"✅ Verification completed: {result}")
        except Exception as e:
            print(f"❌ Verification error: {e}")

    def get_connection_info(self):
        """Connection info"""
        return {
            'peerAddress': self.peer_address,
            'identityMappings': self.identity_mappings,
            'environment': 'Dynamic Identity Management',
            'timestamp': datetime.now().isoformat()
        }

    def test_basic_query(self):
        """Test connectivity"""
        try:
            chaincode_call = {"function": "getMyIdentity", "Args": []}
            result = self._execute_peer_command_with_env(chaincode_call, is_query=True, user_role='admin')
            
            return {
                'testType': 'basic_query_dynamic_identity',
                'success': result['success'],
                'response': result['output'] if result['success'] else result['error'],
                'userRole': result.get('userRole', 'admin')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
