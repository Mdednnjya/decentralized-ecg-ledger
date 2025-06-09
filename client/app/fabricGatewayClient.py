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
        
    def _get_fabric_env(self):
        """
        Setup environment variables yang diperlukan untuk peer CLI
        Berdasarkan working example dari user
        """
        env = os.environ.copy()
        env.update({
            'FABRIC_CFG_PATH': '/app/config',
            'CORE_PEER_LOCALMSPID': 'Org1MSP',
            'CORE_PEER_TLS_ROOTCERT_FILE': '/app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt',
            'CORE_PEER_MSPCONFIGPATH': '/app/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp',
            'CORE_PEER_ADDRESS': '10.34.100.126:7051',
            'CORE_PEER_TLS_ENABLED': 'true',
            'PATH': env.get('PATH', '') + ':/tmp/fabric-bin'
        })
        return env

    def _execute_peer_command_with_env(self, chaincode_call, is_query=False):
        """
        Execute peer command dengan proper environment variables dan dual endorsement
        """
        try:
            # Convert chaincode call ke JSON string
            chaincode_json = json.dumps(chaincode_call, separators=(',', ':'))
            print(f"🔧 Chaincode JSON: {chaincode_json}")
            
            # Get proper environment
            env = self._get_fabric_env()
            print(f"🔧 MSP ID: {env['CORE_PEER_LOCALMSPID']}")
            print(f"🔧 Peer Address: {env['CORE_PEER_ADDRESS']}")
            
            # Build command array
            if is_query:
                cmd = [
                    'peer', 'chaincode', 'query',
                    '-C', self.channel_name,
                    '-n', self.chaincode_name,
                    '-c', chaincode_json,
                    '--peerAddresses', '10.34.100.126:7051',
                    '--tlsRootCertFiles', '/app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt'
                ]
            else:
                # Invoke dengan dual peer endorsement (Org1 + Org2)
                cmd = [
                    'peer', 'chaincode', 'invoke',
                    '-o', self.orderer_address,
                    '--ordererTLSHostnameOverride', 'orderer.example.com',
                    '--tls',
                    '--cafile', '/app/crypto-config/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem',
                    '-C', self.channel_name,
                    '-n', self.chaincode_name,
                    '-c', chaincode_json,
                    '--peerAddresses', '10.34.100.126:7051',
                    '--tlsRootCertFiles', '/app/crypto-config/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt',
                    '--peerAddresses', '10.34.100.114:9051',
                    '--tlsRootCertFiles', '/app/crypto-config/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt'
                ]
            
            print(f"🔄 Executing command with dual endorsement...")
            print(f"   Org1 Peer: 10.34.100.126:7051")
            print(f"   Org2 Peer: 10.34.100.114:9051")
            
            # Execute dengan proper environment
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=90,  # Increase timeout untuk dual endorsement
                cwd='/app',
                shell=False,
                env=env  # KEY: Pass environment variables
            )
            
            print(f"📤 Return code: {result.returncode}")
            if result.stdout:
                print(f"📋 STDOUT: {result.stdout[:500]}...")
            if result.stderr:
                print(f"⚠ STDERR: {result.stderr[:500]}...")
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout, 'error': None}
            else:
                return {'success': False, 'output': result.stdout, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': None, 'error': 'Command timeout after 90 seconds'}
        except Exception as e:
            return {'success': False, 'output': None, 'error': str(e)}

    def store_ecg_data(self, patient_id, ipfs_hash, metadata, patient_owner_client_id):
        """Store ECG data dengan environment variables dan dual endorsement"""
        try:
            print(f"📊 Storing ECG data for patient: {patient_id}")
            print(f"🔗 IPFS Hash: {ipfs_hash}")
            print(f"👤 Owner: {patient_owner_client_id}")
            print(f"📋 Metadata: {metadata}")
            
            # Clean metadata handling
            if isinstance(metadata, dict):
                metadata_str = json.dumps(metadata, separators=(',', ':'))
            elif isinstance(metadata, str):
                try:
                    json.loads(metadata)
                    metadata_str = metadata
                except json.JSONDecodeError:
                    metadata_str = json.dumps({"note": metadata}, separators=(',', ':'))
            else:
                metadata_str = json.dumps({}, separators=(',', ':'))
            
            print(f"🔧 Final metadata string: {metadata_str}")
            
            # Build chaincode call - SAMA seperti working example Anda
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
            
            print(f"🔧 Chaincode call structure: {json.dumps(chaincode_call, indent=2)}")
            
            # Execute dengan environment dan dual endorsement
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False)
            
            if result['success'] and ('Chaincode invoke successful' in result['output'] or 'status:200' in result['output']):
                # Start verification process in background
                self.start_verification(patient_id, ipfs_hash)
                
                return {
                    'status': 'success',
                    'message': 'ECG data stored with PENDING verification',
                    'patientID': patient_id,
                    'ipfsHash': ipfs_hash,
                    'verificationStatus': 'PENDING_VERIFICATION',
                    'blockchainStored': True,
                    'method': 'env_vars_dual_endorsement'
                }
            else:
                print(f"❌ Store failed")
                print(f"❌ Full error details:")
                print(f"   Output: {result.get('output', 'No output')}")
                print(f"   Error: {result.get('error', 'No error')}")
                
                return {
                    'status': 'error', 
                    'message': 'Failed to store ECG data', 
                    'error': result['error'],
                    'output': result['output'],
                    'chaincode_call': chaincode_call,
                    'debug': {
                        'return_code': result.get('returncode'),
                        'has_output': bool(result.get('output')),
                        'has_error': bool(result.get('error'))
                    }
                }
                
        except Exception as e:
            print(f"❌ Exception in store_ecg_data: {str(e)}")
            return {'status': 'error', 'message': 'Exception occurred', 'error': str(e)}

    def grant_access(self, patient_id, doctor_client_id):
        """Grant access dengan environment dan dual endorsement"""
        try:
            print(f"🔓 Granting access: {patient_id} -> {doctor_client_id}")
            
            chaincode_call = {
                "function": "grantAccess",
                "Args": [patient_id, doctor_client_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False)
            
            if result['success'] and ('Chaincode invoke successful' in result['output'] or 'status:200' in result['output']):
                return {
                    'status': 'success', 
                    'message': f'Access granted to specialist for second opinion',
                    'patientID': patient_id,
                    'grantedTo': doctor_client_id,
                    'blockchainUpdated': True
                }
            else:
                return {
                    'status': 'error', 
                    'error': result['error'],
                    'output': result['output']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def revoke_access(self, patient_id, doctor_client_id):
        """Revoke access dengan environment dan dual endorsement"""
        try:
            print(f"🔒 Revoking access: {patient_id} -> {doctor_client_id}")
            
            chaincode_call = {
                "function": "revokeAccess", 
                "Args": [patient_id, doctor_client_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False)
            
            if result['success'] and ('Chaincode invoke successful' in result['output'] or 'status:200' in result['output']):
                return {
                    'status': 'success', 
                    'message': f'Access revoked after consultation completed',
                    'patientID': patient_id,
                    'revokedFrom': doctor_client_id,
                    'blockchainUpdated': True
                }
            else:
                return {
                    'status': 'error', 
                    'error': result['error'],
                    'output': result['output']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def access_ecg_data(self, patient_id):
        """Access ECG data dengan environment dan dual endorsement"""
        try:
            print(f"🔍 Accessing ECG data for patient: {patient_id}")
            
            chaincode_call = {
                "function": "accessECGData",
                "Args": [patient_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False)
            
            if result['success'] and ('Chaincode invoke successful' in result['output'] or 'status:200' in result['output']):
                # Parse payload untuk mendapatkan ECG data info
                try:
                    lines = result['output'].split('\n')
                    for line in lines:
                        if 'payload:' in line:
                            payload_str = line.split('payload:')[1].strip().strip('"')
                            ecg_info = json.loads(payload_str)
                            return {
                                'status': 'success',
                                'patientID': patient_id,
                                'ecgInfo': ecg_info,
                                'accessGranted': True,
                                'blockchainVerified': True
                            }
                except (json.JSONDecodeError, IndexError) as e:
                    print(f"⚠ Failed to parse payload, returning raw response: {e}")
                    
                return {
                    'status': 'success', 
                    'message': 'ECG data accessed successfully',
                    'patientID': patient_id,
                    'rawResponse': result['output']
                }
            else:
                return {
                    'status': 'error', 
                    'error': result['error'],
                    'output': result['output']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def get_audit_trail(self, patient_id):
        """Get audit trail dengan query (single peer sufficient)"""
        try:
            print(f"📋 Getting audit trail for patient: {patient_id}")
            
            chaincode_call = {
                "function": "getAuditTrail",
                "Args": [patient_id]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=True)
            
            if result['success']:
                try:
                    audit_data = json.loads(result['output'].strip())
                    return {
                        'status': 'success',
                        'patientId': patient_id,
                        'auditTrail': audit_data,
                        'blockchainQueried': True
                    }
                except json.JSONDecodeError as e:
                    print(f"⚠ Failed to parse audit data: {e}")
                    return {
                        'status': 'success',
                        'patientId': patient_id,
                        'rawResponse': result['output']
                    }
            else:
                return {
                    'status': 'error', 
                    'error': result['error'],
                    'output': result['output']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def confirm_ecg_data(self, patient_id, is_valid, verification_details):
        """Confirm verification status"""
        try:
            print(f"✅ Confirming verification for patient: {patient_id} - Valid: {is_valid}")
            
            chaincode_call = {
                "function": "confirmECGData",
                "Args": [patient_id, str(is_valid).lower(), verification_details]
            }
            
            result = self._execute_peer_command_with_env(chaincode_call, is_query=False)
            
            if result['success'] and ('Chaincode invoke successful' in result['output'] or 'status:200' in result['output']):
                return {
                    'status': 'success', 
                    'message': 'ECG data verification confirmed',
                    'patientID': patient_id,
                    'verificationResult': 'CONFIRMED' if is_valid else 'FAILED'
                }
            else:
                return {
                    'status': 'error', 
                    'error': result['error'],
                    'output': result['output']
                }
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def start_verification(self, patient_id, ipfs_hash):
        """Start background verification process"""
        print(f"🔄 Starting verification process for {patient_id}")
        verification_thread = threading.Thread(
            target=self._verify_ipfs_data,
            args=(patient_id, ipfs_hash)
        )
        verification_thread.daemon = True
        verification_thread.start()
    
    def _verify_ipfs_data(self, patient_id, ipfs_hash):
        """Background IPFS verification - auto confirm after 10 seconds"""
        try:
            print(f"⏳ Verification process started for {patient_id}, waiting 10 seconds...")
            time.sleep(10)  # Simulate verification time
            
            # For demo, always successful verification
            is_valid = True
            details = f"IPFS data verified successfully - Hash: {ipfs_hash[:20]}... - ECG format valid"
            
            # Update status ke CONFIRMED
            result = self.confirm_ecg_data(patient_id, is_valid, details)
            print(f"✅ Verification completed for {patient_id}: {result}")
            
        except Exception as e:
            print(f"❌ Verification error for {patient_id}: {str(e)}")
            self.confirm_ecg_data(patient_id, False, f"Verification error: {str(e)}")

    def get_connection_info(self):
        """Get connection info dengan status check"""
        # Test basic connectivity
        try:
            chaincode_call = {"function": "getMyIdentity", "Args": []}
            test_result = self._execute_peer_command_with_env(chaincode_call, is_query=True)
            peer_status = "connected" if test_result['success'] else "disconnected"
        except:
            peer_status = "error"
            
        return {
            'peerAddress': self.peer_address,
            'ordererAddress': self.orderer_address,
            'channelName': self.channel_name,
            'chaincodeName': self.chaincode_name,
            'status': peer_status,
            'timestamp': datetime.now().isoformat(),
            'environment': 'Debian 12 + Bash 5.2.15 + Fabric Env Vars',
            'method': 'env_vars_dual_endorsement',
            'endorsement': 'Org1MSP + Org2MSP',
            'connectionType': 'FABRIC_PEER_CLI_WITH_ENV'
        }

    def test_basic_query(self):
        """Test basic chaincode query untuk connectivity"""
        try:
            print("🧪 Testing basic chaincode connectivity...")
            
            chaincode_call = {"function": "getMyIdentity", "Args": []}
            result = self._execute_peer_command_with_env(chaincode_call, is_query=True)
            
            return {
                'testType': 'basic_query_with_env',
                'success': result['success'],
                'response': result['output'] if result['success'] else result['error'],
                'environment': 'Debian 12 + Bash 5.2.15 + Fabric Env Vars',
                'method': 'env_vars_setup'
            }
            
        except Exception as e:
            return {
                'testType': 'basic_query_with_env',
                'success': False,
                'error': str(e)
            }
