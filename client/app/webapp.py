from flask import Flask, jsonify, request
import json
import os
from datetime import datetime

from ipfsClient import IPFSClient
from fabricGatewayClient import FabricGatewayClient

app = Flask(__name__)

# Initialize clients
ipfs_client = IPFSClient(ipfs_host='172.20.1.6', ipfs_port=5001)
fabric_client = FabricGatewayClient(peer_address="10.34.100.126:7051")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint dengan detailed status"""
    ipfs_status = ipfs_client.get_status()
    fabric_info = fabric_client.get_connection_info()
    
    # Test basic blockchain connectivity
    basic_test = fabric_client.test_basic_query()
    
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ipfs": ipfs_status,
            "blockchain": fabric_info,
            "basicConnectivityTest": basic_test
        },
        "features": {
            "escrowPattern": "ENABLED",
            "alertSystem": "ACTIVE",
            "environment": "Debian 12 + Bash 5.2.15 Optimized"
        }
    })

@app.route('/test/connectivity', methods=['GET'])
def test_connectivity():
    """Test endpoint untuk verifikasi konektivitas lengkap"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "environment": "Debian 12 + Bash 5.2.15",
        "tests": {}
    }
    
    # Test IPFS
    try:
        ipfs_test = ipfs_client.get_status()
        results["tests"]["ipfs"] = {
            "status": "PASS" if ipfs_test["status"] == "connected" else "FAIL",
            "details": ipfs_test
        }
    except Exception as e:
        results["tests"]["ipfs"] = {
            "status": "FAIL",
            "error": str(e)
        }
    
    # Test Fabric basic query
    try:
        fabric_test = fabric_client.test_basic_query()
        results["tests"]["fabric_query"] = {
            "status": "PASS" if fabric_test["success"] else "FAIL",
            "details": fabric_test
        }
    except Exception as e:
        results["tests"]["fabric_query"] = {
            "status": "FAIL", 
            "error": str(e)
        }
    
    # Overall status
    all_pass = all(test.get("status") == "PASS" for test in results["tests"].values())
    results["overall"] = "READY" if all_pass else "NOT_READY"
    
    return jsonify(results)

@app.route('/ecg/upload', methods=['POST'])
def upload_ecg():
    """Upload ECG data dengan enhanced error handling dan logging"""
    try:
        print("�� Received ECG upload request")
        data = request.json
        print(f"📋 Request data keys: {list(data.keys()) if data else 'None'}")
        
        patient_id = data.get('patientId')
        ecg_data = data.get('ecgData')
        metadata = data.get('metadata', {})
        patient_owner_id = data.get('patientOwnerClientID', f'x509::CN={patient_id}')
        
        if not patient_id or not ecg_data:
            return jsonify({
                "error": "Missing required fields", 
                "required": ["patientId", "ecgData"],
                "received": list(data.keys()) if data else []
            }), 400
        
        print(f"📊 Processing ECG upload for patient: {patient_id}")
        print(f"👤 Owner will be: {patient_owner_id}")
        print(f"📋 Metadata type: {type(metadata)}")
        
        # Upload to IPFS
        print("🔄 Uploading to IPFS...")
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)
        print(f"✅ IPFS upload successful: {ipfs_hash}")
        
        # Store to blockchain
        print("🔄 Storing metadata to blockchain...")
        blockchain_result = fabric_client.store_ecg_data(patient_id, ipfs_hash, metadata, patient_owner_id)
        print(f"📤 Blockchain result status: {blockchain_result.get('status')}")
        
        if blockchain_result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": "ECG data uploaded successfully with escrow protection",
                "patientId": patient_id,
                "ipfsHash": ipfs_hash,
                "blockchainResult": blockchain_result,
                "verificationStatus": "PENDING_VERIFICATION",
                "note": "Data will be automatically verified within 10 seconds",
                "environment": "Debian 12 + Bash 5.2.15 Optimized"
            })
        else:
            return jsonify({
                "status": "partial_success",
                "message": "IPFS upload successful but blockchain storage failed",
                "patientId": patient_id,
                "ipfsHash": ipfs_hash,
                "blockchainError": blockchain_result,
                "recommendation": "Check blockchain connectivity and try again",
                "environment": "Debian 12 + Bash 5.2.15"
            }), 500
        
    except Exception as e:
        print(f"❌ Error in upload_ecg: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "endpoint": "/ecg/upload"
        }), 500

@app.route('/ecg/grant-access', methods=['POST'])
def grant_access():
    """Grant access dengan detailed logging"""
    try:
        print("🔓 Received grant access request")
        data = request.json
        
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID')
        
        if not patient_id or not doctor_id:
            return jsonify({
                "error": "Missing required fields",
                "required": ["patientId", "doctorClientID"],
                "received": list(data.keys()) if data else []
            }), 400
        
        print(f"🔓 Granting access: Patient {patient_id} -> Doctor {doctor_id}")
        
        result = fabric_client.grant_access(patient_id, doctor_id)
        print(f"📤 Grant access result status: {result.get('status')}")
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": "Access granted successfully for second opinion consultation",
                "patientId": patient_id,
                "grantedTo": doctor_id,
                "result": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to grant access",
                "error": result,
                "recommendation": "Verify patient ownership and blockchain connectivity"
            }), 500
        
    except Exception as e:
        print(f"❌ Error in grant_access: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "endpoint": "/ecg/grant-access"
        }), 500

@app.route('/ecg/revoke-access', methods=['POST'])
def revoke_access():
    """Revoke access dengan detailed logging"""
    try:
        print("🔒 Received revoke access request")
        data = request.json
        
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID')
        
        if not patient_id or not doctor_id:
            return jsonify({
                "error": "Missing required fields",
                "required": ["patientId", "doctorClientID"],
                "received": list(data.keys()) if data else []
            }), 400
        
        print(f"🔒 Revoking access: Patient {patient_id} -> Doctor {doctor_id}")
        
        result = fabric_client.revoke_access(patient_id, doctor_id)
        print(f"📤 Revoke access result status: {result.get('status')}")
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": "Access revoked successfully after consultation completion",
                "patientId": patient_id,
                "revokedFrom": doctor_id,
                "result": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to revoke access",
                "error": result,
                "recommendation": "Verify patient ownership and blockchain connectivity"
            }), 500
        
    except Exception as e:
        print(f"❌ Error in revoke_access: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "endpoint": "/ecg/revoke-access"
        }), 500

@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg(patient_id):
    """Access ECG data dengan detailed logging"""
    try:
        print(f"🔍 Received access request for patient: {patient_id}")
        
        result = fabric_client.access_ecg_data(patient_id)
        print(f"📤 Access result status: {result.get('status')}")
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": "ECG data accessed successfully",
                "patientId": patient_id,
                "result": result,
                "note": "Access has been recorded in audit trail"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to access ECG data",
                "patientId": patient_id,
                "error": result,
                "possibleReasons": [
                    "Data not yet verified (still in PENDING status)",
                    "Access not granted by patient", 
                    "Patient ID not found",
                    "Blockchain connectivity issue"
                ]
            }), 403
        
    except Exception as e:
        print(f"❌ Error in access_ecg: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "endpoint": f"/ecg/access/{patient_id}"
        }), 500

@app.route('/ecg/audit/<patient_id>', methods=['GET'])
def get_audit_trail(patient_id):
    """Get audit trail dengan detailed logging"""
    try:
        print(f"📋 Received audit trail request for patient: {patient_id}")
        
        result = fabric_client.get_audit_trail(patient_id)
        print(f"📤 Audit trail result status: {result.get('status')}")
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": "Audit trail retrieved successfully",
                "patientId": patient_id,
                "result": result,
                "note": "Complete transparency of all data access activities"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to retrieve audit trail",
                "patientId": patient_id,
                "error": result,
                "possibleReasons": [
                    "Only patient owner can view audit trail",
                    "Patient ID not found",
                    "Blockchain connectivity issue"
                ]
            }), 403
        
    except Exception as e:
        print(f"❌ Error in get_audit_trail: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "endpoint": f"/ecg/audit/{patient_id}"
        }), 500

@app.route('/demo/test-case/<case_name>', methods=['GET'])
def get_demo_test_case(case_name):
    """Endpoint untuk mendapatkan contoh curl command untuk demo"""
    
    base_url = "http://10.34.100.125:3000"  # Client VM IP
    
    test_cases = {
        "health": {
            "description": "Test health check dan connectivity",
            "curl": f"curl -X GET {base_url}/health | jq ."
        },
        
        "connectivity": {
            "description": "Test konektivitas lengkap IPFS dan Blockchain",
            "curl": f"curl -X GET {base_url}/test/connectivity | jq ."
        },
        
        "upload_maria": {
            "description": "Case: Dr. Sarah menyimpan ECG data Maria (35 tahun, nyeri dada)",
            "curl": f'''curl -X POST {base_url}/ecg/upload \\
  -H "Content-Type: application/json" \\
  -d '{{
    "patientId": "MARIA001",
    "patientOwnerClientID": "x509::CN=maria.patient",
    "ecgData": {{
      "patientInfo": {{
        "id": "MARIA001",
        "age": 35,
        "gender": "F",
        "symptoms": "chest pain"
      }},
      "recordInfo": {{
        "deviceId": "ECG-RSJ-001",
        "timestamp": "2025-06-09T08:00:00Z",
        "samplingRate": 500,
        "duration": 30
      }},
      "leads": {{
        "I": [0.1, 0.2, 0.5, 0.7, 0.8, 0.7, 0.5, 0.3, 0.1, 0.0],
        "II": [0.2, 0.3, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.2, 0.1],
        "aVR": [-0.15, -0.25, -0.55, -0.75, -0.85, -0.75, -0.55, -0.35, -0.15, -0.05]
      }},
      "analysis": {{
        "heartRate": 78,
        "rhythm": "sinus",
        "abnormalities": "ST elevation in leads II, III, aVF"
      }}
    }},
    "metadata": {{
      "hospital": "RS Jakarta",
      "doctor": "Dr. Sarah",
      "department": "Emergency",
      "priority": "high"
    }}
  }}' | jq .'''
        },
        
        "grant_access": {
            "description": "Case: Maria memberikan akses ke Dr. Ahmad untuk second opinion",
            "curl": f'''curl -X POST {base_url}/ecg/grant-access \\
  -H "Content-Type: application/json" \\
  -d '{{
    "patientId": "MARIA001",
    "doctorClientID": "x509::CN=dr.ahmad.cardiologist"
  }}' | jq .'''
        },
        
        "access_data": {
            "description": "Case: Dr. Ahmad mengakses ECG data Maria untuk second opinion",
            "curl": f"curl -X GET {base_url}/ecg/access/MARIA001 | jq ."
        },
        
        "revoke_access": {
            "description": "Case: Maria mencabut akses Dr. Ahmad setelah konsultasi selesai",
            "curl": f'''curl -X POST {base_url}/ecg/revoke-access \\
  -H "Content-Type: application/json" \\
  -d '{{
    "patientId": "MARIA001",
    "doctorClientID": "x509::CN=dr.ahmad.cardiologist"
  }}' | jq .'''
        },
        
        "audit_trail": {
            "description": "Case: Maria melihat audit trail semua aktivitas data ECG nya",
            "curl": f"curl -X GET {base_url}/ecg/audit/MARIA001 | jq ."
        }
    }
    
    if case_name in test_cases:
        return jsonify({
            "testCase": case_name,
            "description": test_cases[case_name]["description"],
            "curlCommand": test_cases[case_name]["curl"],
            "note": "Copy paste command di atas ke terminal untuk testing",
            "workflow": "Jalankan test cases secara berurutan untuk simulasi lengkap"
        })
    else:
        available_cases = list(test_cases.keys())
        return jsonify({
            "error": "Test case not found",
            "availableCases": available_cases,
            "usage": f"GET /demo/test-case/<case_name>",
            "example": f"GET /demo/test-case/health"
        }), 404

@app.route('/demo/workflow', methods=['GET'])
def get_demo_workflow():
    """Endpoint untuk mendapatkan complete workflow demo"""
    
    base_url = "http://10.34.100.125:3000"
    
    return jsonify({
        "title": "ECG Blockchain System - Complete Demo Workflow",
        "description": "Simulasi lengkap use case Maria (35 tahun, nyeri dada)",
        "baseURL": base_url,
        "environment": "Debian 12 + Bash 5.2.15 Optimized",
        "workflow": [
            {
                "step": 1,
                "title": "Health Check",
                "description": "Verifikasi sistem siap digunakan",
                "command": f"curl -X GET {base_url}/health | jq .",
                "expectedResult": "status: UP, IPFS connected, blockchain connected"
            },
            {
                "step": 2,
                "title": "Test Connectivity",  
                "description": "Test konektivitas lengkap",
                "command": f"curl -X GET {base_url}/test/connectivity | jq .",
                "expectedResult": "overall: READY, all tests PASS"
            },
            {
                "step": 3,
                "title": "Dr. Sarah Upload ECG Maria",
                "description": "Doctor menyimpan ECG data dengan patient sebagai owner",
                "command": f"curl -X GET {base_url}/demo/test-case/upload_maria | jq -r .curlCommand",
                "expectedResult": "PENDING_VERIFICATION status, verification starts automatically"
            },
            {
                "step": 4,
                "title": "Wait for Verification (10 detik)",
                "description": "Background process verifikasi IPFS data",
                "command": "sleep 12 && echo 'Verification should be complete'",
                "expectedResult": "Data status berubah dari PENDING ke CONFIRMED"
            },
            {
                "step": 5,
                "title": "Maria Grant Access ke Dr. Ahmad",
                "description": "Patient memberikan akses untuk second opinion", 
                "command": f"curl -X GET {base_url}/demo/test-case/grant_access | jq -r .curlCommand",
                "expectedResult": "Access granted successfully"
            },
            {
                "step": 6,
                "title": "Dr. Ahmad Access ECG Data",
                "description": "Specialist mengakses data untuk konsultasi",
                "command": f"curl -X GET {base_url}/demo/test-case/access_data | jq -r .curlCommand", 
                "expectedResult": "ECG data retrieved, access recorded in audit trail"
            },
            {
                "step": 7,
                "title": "Maria Revoke Access",
                "description": "Patient mencabut akses setelah konsultasi selesai",
                "command": f"curl -X GET {base_url}/demo/test-case/revoke_access | jq -r .curlCommand",
                "expectedResult": "Access revoked successfully"
            },
            {
                "step": 8,
                "title": "Maria Check Audit Trail",
                "description": "Patient melihat transparansi semua aktivitas",
                "command": f"curl -X GET {base_url}/demo/test-case/audit_trail | jq -r .curlCommand",
                "expectedResult": "Complete audit log of all access activities"
            }
        ],
        "notes": [
            "Jalankan setiap step secara berurutan",
            "Tunggu 10+ detik setelah upload sebelum grant access",
            "Monitor container logs untuk real-time events",
            "Setiap step merekam aktivitas di blockchain",
            "Menggunakan file-based approach untuk reliable JSON handling"
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting ECG Blockchain System...")
    print("📋 Available endpoints:")
    print("  - GET  /health (System health check)")
    print("  - GET  /test/connectivity (Full connectivity test)")
    print("  - POST /ecg/upload (Dr. Sarah stores Maria's ECG)")
    print("  - POST /ecg/grant-access (Maria grants access to Dr. Ahmad)")
    print("  - GET  /ecg/access/<patient_id> (Dr. Ahmad accesses ECG)")
    print("  - POST /ecg/revoke-access (Maria revokes access)")
    print("  - GET  /ecg/audit/<patient_id> (View audit trail)")
    print("  - GET  /demo/workflow (Get complete demo workflow)")
    print("  - GET  /demo/test-case/<case_name> (Get specific test commands)")
    print("\n⛓  Blockchain: Hyperledger Fabric")
    print("🔒 Escrow Pattern: ENABLED") 
    print("🛠 Environment: Debian 12 + Bash 5.2.15 Optimized")
    print("📁 Method: File-based JSON handling untuk reliable chaincode calls")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
