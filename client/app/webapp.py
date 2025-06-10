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

def get_user_role():
    """Extract user role from header dengan default fallback"""
    user_role = request.headers.get('X-User-Role', 'admin').lower()
    if user_role not in ['patient', 'doctor', 'admin']:
        user_role = 'admin'
    return user_role

def get_patient_owner_id(user_role):
    """Generate patient owner ID berdasarkan role"""
    if user_role == 'patient':
        return "x509::/C=US/ST=California/L=San Francisco/OU=client/CN=User1@org1.example.com::/C=US/ST=California/L=San Francisco/O=org1.example.com/CN=ca.org1.example.com"
    else:
        return "x509::/C=US/ST=California/L=San Francisco/OU=client/CN=User1@org1.example.com::/C=US/ST=California/L=San Francisco/O=org1.example.com/CN=ca.org1.example.com"

def get_doctor_id():
    """Generate doctor ID untuk authorization"""
    return "x509::/C=US/ST=California/L=San Francisco/OU=client/CN=User1@org2.example.com::/C=US/ST=California/L=San Francisco/O=org2.example.com/CN=ca.org2.example.com"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check dengan identity info"""
    user_role = get_user_role()
    ipfs_status = ipfs_client.get_status()
    fabric_info = fabric_client.get_connection_info()
    
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "currentUserRole": user_role,
        "services": {
            "ipfs": ipfs_status,
            "blockchain": fabric_info
        },
        "features": {
            "dynamicIdentity": "ENABLED",
            "escrowPattern": "ENABLED",
            "environment": "Multi-Role Authentication"
        }
    })

@app.route('/test/connectivity', methods=['GET'])
def test_connectivity():
    """Test connectivity dengan current user role"""
    user_role = get_user_role()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "currentUserRole": user_role,
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
        results["tests"]["ipfs"] = {"status": "FAIL", "error": str(e)}
    
    # Test Fabric dengan current role
    try:
        fabric_test = fabric_client.test_basic_query()
        results["tests"]["fabric_identity"] = {
            "status": "PASS" if fabric_test["success"] else "FAIL",
            "details": fabric_test,
            "userRole": user_role
        }
    except Exception as e:
        results["tests"]["fabric_identity"] = {"status": "FAIL", "error": str(e)}
    
    # Overall status
    all_pass = all(test.get("status") == "PASS" for test in results["tests"].values())
    results["overall"] = "READY" if all_pass else "NOT_READY"
    
    return jsonify(results)

@app.route('/ecg/upload', methods=['POST'])
def upload_ecg():
    """Upload ECG dengan role-based identity"""
    try:
        user_role = get_user_role()
        print(f"📊 ECG Upload request by {user_role}")
        
        data = request.json
        patient_id = data.get('patientId')
        ecg_data = data.get('ecgData')
        metadata = data.get('metadata', {})
        
        # Override patient owner berdasarkan role
        patient_owner_id = data.get('patientOwnerClientID') or get_patient_owner_id(user_role)
        
        if not patient_id or not ecg_data:
            return jsonify({
                "error": "Missing required fields", 
                "required": ["patientId", "ecgData"],
                "received": list(data.keys()) if data else []
            }), 400
        
        print(f"📊 Processing: Patient {patient_id} by {user_role}")
        
        # Upload to IPFS
        ipfs_hash = ipfs_client.upload_ecg_data(ecg_data)
        print(f"✅ IPFS: {ipfs_hash}")
        
        # Store to blockchain dengan role
        blockchain_result = fabric_client.store_ecg_data(
            patient_id, ipfs_hash, metadata, patient_owner_id, user_role
        )
        
        if blockchain_result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": f"ECG uploaded by {user_role}",
                "patientId": patient_id,
                "ipfsHash": ipfs_hash,
                "userRole": user_role,
                "blockchainResult": blockchain_result,
                "verificationStatus": "PENDING_VERIFICATION"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Blockchain storage failed",
                "userRole": user_role,
                "error": blockchain_result
            }), 500
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "endpoint": "/ecg/upload"
        }), 500

@app.route('/ecg/grant-access', methods=['POST'])
def grant_access():
    """Grant access dengan patient identity validation"""
    try:
        user_role = get_user_role()
        print(f"🔓 Grant access request by {user_role}")
        
        data = request.json
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID') or get_doctor_id()
        
        if not patient_id:
            return jsonify({
                "error": "Missing patientId",
                "userRole": user_role
            }), 400
        
        # Force patient role untuk grant access
        if user_role != 'patient':
            return jsonify({
                "status": "error",
                "message": "Only patients can grant access to their data",
                "userRole": user_role,
                "requiredRole": "patient",
                "hint": "Use header: X-User-Role: patient"
            }), 403
        
        result = fabric_client.grant_access(patient_id, doctor_id, user_role)
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": f"Access granted by {user_role}",
                "patientId": patient_id,
                "grantedTo": doctor_id,
                "userRole": user_role,
                "result": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to grant access",
                "userRole": user_role,
                "error": result
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "userRole": get_user_role()
        }), 500

@app.route('/ecg/access/<patient_id>', methods=['GET'])
def access_ecg_data(patient_id):
    """Access ECG dengan role validation"""
    try:
        user_role = get_user_role()
        print(f"📖 Access request: Patient {patient_id} by {user_role}")
        
        result = fabric_client.access_ecg_data(patient_id, user_role)
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": f"ECG data accessed by {user_role}",
                "patientId": patient_id,
                "userRole": user_role,
                "data": result.get('data'),
                "accessRecorded": True
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Access denied or data not found",
                "patientId": patient_id,
                "userRole": user_role,
                "error": result,
                "possibleReasons": [
                    "Data not verified yet",
                    "Access not granted",
                    "Wrong user role",
                    "Patient ID not found"
                ]
            }), 403
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "userRole": get_user_role()
        }), 500

@app.route('/ecg/revoke-access', methods=['POST'])
def revoke_access():
    """Revoke access dengan patient identity validation"""
    try:
        user_role = get_user_role()
        print(f"🔒 Revoke access request by {user_role}")
        
        data = request.json
        patient_id = data.get('patientId')
        doctor_id = data.get('doctorClientID') or get_doctor_id()
        
        if not patient_id:
            return jsonify({
                "error": "Missing patientId",
                "userRole": user_role
            }), 400
        
        # Force patient role untuk revoke access
        if user_role != 'patient':
            return jsonify({
                "status": "error",
                "message": "Only patients can revoke access to their data",
                "userRole": user_role,
                "requiredRole": "patient",
                "hint": "Use header: X-User-Role: patient"
            }), 403
        
        result = fabric_client.revoke_access(patient_id, doctor_id, user_role)
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": f"Access revoked by {user_role}",
                "patientId": patient_id,
                "revokedFrom": doctor_id,
                "userRole": user_role,
                "result": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to revoke access",
                "userRole": user_role,
                "error": result
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "userRole": get_user_role()
        }), 500

@app.route('/ecg/audit/<patient_id>', methods=['GET'])
def get_audit_trail(patient_id):
    """Get audit trail dengan role validation"""
    try:
        user_role = get_user_role()
        print(f"📋 Audit request: Patient {patient_id} by {user_role}")
        
        result = fabric_client.get_audit_trail(patient_id, user_role)
        
        if result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "message": f"Audit trail retrieved by {user_role}",
                "patientId": patient_id,
                "userRole": user_role,
                "auditTrail": result.get('auditTrail'),
                "transparency": "Full access history displayed"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to retrieve audit trail",
                "patientId": patient_id,
                "userRole": user_role,
                "error": result
            }), 403
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "userRole": get_user_role()
        }), 500

if __name__ == '__main__':
    print("🚀 ECG Blockchain System - Multi-Role Authentication")
    print("📋 Available endpoints:")
    print("  - GET  /health")
    print("  - GET  /test/connectivity")
    print("  - POST /ecg/upload")
    print("  - POST /ecg/grant-access")
    print("  - GET  /ecg/access/<patient_id>")
    print("  - POST /ecg/revoke-access")
    print("  - GET  /ecg/audit/<patient_id>")
    print("")
    print("🔐 Role-based Authentication:")
    print("  - Header: X-User-Role: patient|doctor|admin")
    print("  - Default: admin")
    print("")
    print("⛓  Network: ECG Healthcare Consortium")
    print("🔒 Security: Dynamic Identity Management")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
