'use strict';

const { Contract } = require('fabric-contract-api');

class ECGContract extends Contract {

    // Helper method to get the client ID (X.509 identity string)
    getClientIdentityString(ctx) {
        return ctx.clientIdentity.getID();
    }

    async initLedger(ctx) {
        console.info('========= ECG Chaincode Initialized =========');
        return;
    }

    async storeECGData(ctx, patientIDString, ipfsHash, timestamp, metadata, patientOwnerClientID) {
        console.info('========= Store ECG Data with Escrow Pattern =========');

        // Doctor yang input data
        const inputByClientID = this.getClientIdentityString(ctx);

        // Patient yang menjadi owner data
        if (!patientOwnerClientID || patientOwnerClientID.trim() === '') {
            throw new Error('Patient owner client ID is required');
        }

        const parsedMetadata = JSON.parse(metadata || '{}');
        
        // 🔧 FIX: Use deterministic timestamp from parameter
        const deterministicTimestamp = timestamp || new Date().toISOString();
        
        const ecgData = {
            patientID: patientIDString,
            ipfsHash,
            timestamp: deterministicTimestamp,
            metadata: parsedMetadata,
            status: "PENDING_VERIFICATION",      // 🔒 Escrow: Start with PENDING
            accessControl: {
                owner: patientOwnerClientID,      // Patient sebagai owner
                authorizedUsers: []              // Awalnya kosong
            },
            accessHistory: [],
            inputBy: inputByClientID,             // Doctor yang input data
            createdAt: deterministicTimestamp,   // 🔧 FIX: Use deterministic timestamp
            lastStatusUpdate: deterministicTimestamp  // 🔧 FIX: Use deterministic timestamp
        };

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`ECG data stored with PENDING status for patient ${patientIDString} with owner ${patientOwnerClientID}, input by ${inputByClientID}`);
        
        // 🚨 EMIT EVENT untuk notification system
        const eventPayload = {
            eventType: 'ECG_DATA_STORED',
            patientID: patientIDString,
            ipfsHash: ipfsHash,
            timestamp: deterministicTimestamp,
            status: "PENDING_VERIFICATION",
            hospital: parsedMetadata.hospital || 'Unknown Hospital',
            doctor: parsedMetadata.doctor || 'Unknown Doctor',
            device: parsedMetadata.device || 'Unknown Device',
            inputBy: inputByClientID,
            owner: patientOwnerClientID,
            notificationMessage: `New ECG data uploaded for patient ${patientIDString} - Awaiting verification`
        };

        ctx.stub.setEvent('ECGDataStored', Buffer.from(JSON.stringify(eventPayload)));
        console.info(`Event emitted: ECGDataStored for patient ${patientIDString}`);

        // 🔄 EMIT EVENT untuk IPFS verification
        const verificationPayload = {
            eventType: 'VERIFY_IPFS_DATA',
            patientID: patientIDString,
            ipfsHash: ipfsHash,
            timestamp: deterministicTimestamp,
            requestedBy: inputByClientID,
            verificationTimeout: 300 // 5 minutes timeout
        };

        ctx.stub.setEvent('VerifyIPFSData', Buffer.from(JSON.stringify(verificationPayload)));
        console.info(`Event emitted: VerifyIPFSData for patient ${patientIDString}`);
        
        return JSON.stringify({ 
            status: 'success', 
            message: 'ECG data stored successfully with PENDING verification status', 
            patientID: patientIDString, 
            owner: patientOwnerClientID,
            inputBy: inputByClientID,
            verificationStatus: "PENDING_VERIFICATION",
            eventEmitted: true
        });
    }

    async confirmECGData(ctx, patientIDString, isValid, verificationDetails) {
        console.info('========= Confirm ECG Data Verification =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const verifierClientID = this.getClientIdentityString(ctx);

        // Only allow verification if status is PENDING
        if (ecgData.status !== "PENDING_VERIFICATION") {
            throw new Error(`ECG data for patient ${patientIDString} is not in PENDING_VERIFICATION status. Current status: ${ecgData.status}`);
        }

        // 🔧 FIX: Use transaction timestamp for deterministic behavior
        const txTimestamp = ctx.stub.getTxTimestamp();
        const deterministicTimestamp = new Date(txTimestamp.seconds * 1000 + Math.round(txTimestamp.nanos / 1000000)).toISOString();

        // Update status based on verification result
        const newStatus = (isValid === 'true' || isValid === true) ? "CONFIRMED" : "FAILED";
        ecgData.status = newStatus;
        ecgData.lastStatusUpdate = deterministicTimestamp;  // 🔧 FIX: Use transaction timestamp
        ecgData.verificationDetails = {
            verifiedBy: verifierClientID,
            verifiedAt: deterministicTimestamp,  // 🔧 FIX: Use transaction timestamp
            isValid: newStatus === "CONFIRMED",
            details: verificationDetails || "Automated verification"
        };

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`ECG data for patient ${patientIDString} verification completed. Status: ${newStatus}`);

        // 🚨 EMIT EVENT untuk verification result
        const eventPayload = {
            eventType: 'ECG_VERIFICATION_COMPLETED',
            patientID: patientIDString,
            verificationResult: newStatus,
            verifiedBy: verifierClientID,
            timestamp: deterministicTimestamp,
            ipfsHash: ecgData.ipfsHash,
            notificationMessage: `ECG data verification ${newStatus.toLowerCase()} for patient ${patientIDString}`
        };

        ctx.stub.setEvent('ECGVerificationCompleted', Buffer.from(JSON.stringify(eventPayload)));
        console.info(`Event emitted: ECGVerificationCompleted for patient ${patientIDString} with result ${newStatus}`);

        return JSON.stringify({
            status: 'success',
            message: `ECG data verification completed for patient ${patientIDString}`,
            verificationResult: newStatus,
            verifiedBy: verifierClientID,
            verifiedAt: ecgData.verificationDetails.verifiedAt
        });
    }

    async grantAccess(ctx, patientIDString, doctorClientIDToGrant) {
        console.info('========= Grant Access =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const callerClientID = this.getClientIdentityString(ctx);

        // Check if data is verified before allowing access grants
        if (ecgData.status !== "CONFIRMED") {
            throw new Error(`Cannot grant access to unverified ECG data. Current status: ${ecgData.status}. Data must be CONFIRMED first.`);
        }

        // Hanya owner (patient) yang bisa memberikan akses
        if (callerClientID !== ecgData.accessControl.owner) {
            console.error(`Unauthorized grant attempt: Caller ${callerClientID} is not owner ${ecgData.accessControl.owner} of patient ${patientIDString}`);
            throw new Error(`Only the patient owner (${ecgData.accessControl.owner}) can grant access to their data. Current caller: ${callerClientID}`);
        }

        // Check if doctor already has access
        if (ecgData.accessControl.authorizedUsers.includes(doctorClientIDToGrant)) {
            throw new Error(`Doctor ${doctorClientIDToGrant} already has access to patient ${patientIDString} data`);
        }

        // Grant access
        ecgData.accessControl.authorizedUsers.push(doctorClientIDToGrant);
        
        // 🔧 FIX: Use transaction timestamp for deterministic behavior
        const txTimestamp = ctx.stub.getTxTimestamp();
        const deterministicTimestamp = new Date(txTimestamp.seconds * 1000 + Math.round(txTimestamp.nanos / 1000000)).toISOString();
        
        ecgData.lastStatusUpdate = deterministicTimestamp;  // 🔧 FIX: Use transaction timestamp

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`Access granted to doctor ${doctorClientIDToGrant} for patient ${patientIDString} by owner ${callerClientID}`);

        // 🚨 EMIT EVENT untuk access grant notification
        const eventPayload = {
            eventType: 'ACCESS_GRANTED',
            patientID: patientIDString,
            grantedTo: doctorClientIDToGrant,
            grantedBy: callerClientID,
            timestamp: deterministicTimestamp,
            ipfsHash: ecgData.ipfsHash,
            notificationMessage: `Access granted to ${doctorClientIDToGrant} for patient ${patientIDString}`
        };

        ctx.stub.setEvent('AccessGranted', Buffer.from(JSON.stringify(eventPayload)));
        console.info(`Event emitted: AccessGranted for doctor ${doctorClientIDToGrant} to patient ${patientIDString}`);

        return JSON.stringify({
            status: 'success',
            message: `Access granted to doctor ${doctorClientIDToGrant} for patient ${patientIDString}`,
            grantedBy: callerClientID,
            grantedTo: doctorClientIDToGrant,
            currentAuthorizedUsers: ecgData.accessControl.authorizedUsers
        });
    }

    async revokeAccess(ctx, patientIDString, doctorClientIDToRevoke) {
        console.info('========= Revoke Access =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const callerClientID = this.getClientIdentityString(ctx);

        // Hanya owner (patient) yang bisa mencabut akses
        if (callerClientID !== ecgData.accessControl.owner) {
            console.error(`Unauthorized revoke attempt: Caller ${callerClientID} is not owner ${ecgData.accessControl.owner} of patient ${patientIDString}`);
            throw new Error(`Only the patient owner (${ecgData.accessControl.owner}) can revoke access to their data. Current caller: ${callerClientID}`);
        }

        // Check if doctor has access
        const doctorIndex = ecgData.accessControl.authorizedUsers.indexOf(doctorClientIDToRevoke);
        if (doctorIndex === -1) {
            throw new Error(`Doctor ${doctorClientIDToRevoke} does not have access to patient ${patientIDString} data`);
        }

        // Revoke access
        ecgData.accessControl.authorizedUsers.splice(doctorIndex, 1);
        
        // 🔧 FIX: Use transaction timestamp for deterministic behavior
        const txTimestamp = ctx.stub.getTxTimestamp();
        const deterministicTimestamp = new Date(txTimestamp.seconds * 1000 + Math.round(txTimestamp.nanos / 1000000)).toISOString();
        
        ecgData.lastStatusUpdate = deterministicTimestamp;  // 🔧 FIX: Use transaction timestamp

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`Access revoked from doctor ${doctorClientIDToRevoke} for patient ${patientIDString} by owner ${callerClientID}`);

        // 🚨 EMIT EVENT untuk access revoke notification
        const eventPayload = {
            eventType: 'ACCESS_REVOKED',
            patientID: patientIDString,
            revokedFrom: doctorClientIDToRevoke,
            revokedBy: callerClientID,
            timestamp: deterministicTimestamp,
            ipfsHash: ecgData.ipfsHash,
            notificationMessage: `Access revoked from ${doctorClientIDToRevoke} for patient ${patientIDString}`
        };

        ctx.stub.setEvent('AccessRevoked', Buffer.from(JSON.stringify(eventPayload)));
        console.info(`Event emitted: AccessRevoked for doctor ${doctorClientIDToRevoke} from patient ${patientIDString}`);

        return JSON.stringify({
            status: 'success',
            message: `Access revoked from doctor ${doctorClientIDToRevoke} for patient ${patientIDString}`,
            revokedBy: callerClientID,
            revokedFrom: doctorClientIDToRevoke,
            currentAuthorizedUsers: ecgData.accessControl.authorizedUsers
        });
    }

    async accessECGData(ctx, patientIDString) {
        console.info('========= Access ECG Data =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const accessorClientID = this.getClientIdentityString(ctx);

        // Check if data is confirmed/verified before allowing access
        if (ecgData.status !== "CONFIRMED") {
            throw new Error(`ECG data for patient ${patientIDString} is not verified. Current status: ${ecgData.status}. Only CONFIRMED data can be accessed.`);
        }

        // Check access permissions
        const isOwner = (accessorClientID === ecgData.accessControl.owner);
        const isAuthorized = ecgData.accessControl.authorizedUsers.includes(accessorClientID);

        if (!isOwner && !isAuthorized) {
            console.error(`Unauthorized access attempt: Accessor ${accessorClientID} is not authorized for patient ${patientIDString}`);
            console.error(`Owner: ${ecgData.accessControl.owner}`);
            console.error(`Authorized users: ${JSON.stringify(ecgData.accessControl.authorizedUsers)}`);
            throw new Error(`Access denied. Only the patient owner or authorized doctors can access this ECG data.`);
        }

        // 🔧 FIX: Use transaction timestamp for deterministic behavior
        const txTimestamp = ctx.stub.getTxTimestamp();
        const deterministicTimestamp = new Date(txTimestamp.seconds * 1000 + Math.round(txTimestamp.nanos / 1000000)).toISOString();

        // Log access in audit trail
        const accessRecord = {
            accessorID: accessorClientID,
            accessTime: deterministicTimestamp,  // 🔧 FIX: Use transaction timestamp
            accessType: isOwner ? 'OWNER_ACCESS' : 'AUTHORIZED_ACCESS',
            ipfsHash: ecgData.ipfsHash
        };

        ecgData.accessHistory.push(accessRecord);
        ecgData.lastStatusUpdate = deterministicTimestamp;  // 🔧 FIX: Use transaction timestamp

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`ECG data accessed by ${accessorClientID} for patient ${patientIDString} (${accessRecord.accessType})`);

        // 🚨 EMIT EVENT untuk access log
        const eventPayload = {
            eventType: 'ECG_DATA_ACCESSED',
            patientID: patientIDString,
            accessedBy: accessorClientID,
            accessType: accessRecord.accessType,
            timestamp: deterministicTimestamp,
            ipfsHash: ecgData.ipfsHash,
            notificationMessage: `ECG data accessed by ${accessorClientID} for patient ${patientIDString}`
        };

        ctx.stub.setEvent('ECGDataAccessed', Buffer.from(JSON.stringify(eventPayload)));
        console.info(`Event emitted: ECGDataAccessed by ${accessorClientID} for patient ${patientIDString}`);

        return JSON.stringify({
            patientID: ecgData.patientID,
            ipfsHash: ecgData.ipfsHash,
            timestamp: ecgData.timestamp,
            metadata: ecgData.metadata,
            status: ecgData.status,
            accessorType: accessRecord.accessType,
            accessTime: accessRecord.accessTime,
            verificationDetails: ecgData.verificationDetails
        });
    }

    async getDataStatus(ctx, patientIDString) {
        console.info('========= Get Data Status =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const accessorClientID = this.getClientIdentityString(ctx);

        // Only allow authorized parties to check status
        const isOwner = (accessorClientID === ecgData.accessControl.owner);
        const isAuthorized = ecgData.accessControl.authorizedUsers.includes(accessorClientID);
        
        if (!isOwner && !isAuthorized) {
            throw new Error(`Access denied. Only the patient owner or authorized doctors can check data status.`);
        }

        return JSON.stringify({
            patientID: ecgData.patientID,
            status: ecgData.status,
            createdAt: ecgData.createdAt,
            lastStatusUpdate: ecgData.lastStatusUpdate,
            verificationDetails: ecgData.verificationDetails || null,
            accessibleForDataAccess: ecgData.status === "CONFIRMED"
        });
    }

    async getAuditTrail(ctx, patientIDString) {
        console.info('========= Get Audit Trail =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const accessorClientID = this.getClientIdentityString(ctx);

        // Hanya owner (patient) yang bisa melihat audit trail lengkap
        if (accessorClientID !== ecgData.accessControl.owner) {
            console.error(`Unauthorized audit trail access attempt: Accessor ${accessorClientID} is not owner ${ecgData.accessControl.owner} for patient ${patientIDString}`);
            throw new Error(`Only the patient owner can view the complete audit trail. Owner: ${ecgData.accessControl.owner}`);
        }
        
        console.info(`Audit trail accessed by owner ${accessorClientID} for patient ${patientIDString}`);
        return JSON.stringify({
            patientID: patientIDString,
            currentStatus: ecgData.status,
            auditTrail: ecgData.accessHistory,
            currentAuthorizedUsers: ecgData.accessControl.authorizedUsers,
            dataInputBy: ecgData.inputBy,
            owner: ecgData.accessControl.owner,
            verificationDetails: ecgData.verificationDetails,
            createdAt: ecgData.createdAt,
            lastStatusUpdate: ecgData.lastStatusUpdate
        });
    }

    // Helper function untuk debugging identity
    async getMyIdentity(ctx) {
        const clientID = ctx.clientIdentity.getID();
        console.info(`Client ID requesting is: ${clientID}`);
        return clientID;
    }
}

module.exports = ECGContract;
