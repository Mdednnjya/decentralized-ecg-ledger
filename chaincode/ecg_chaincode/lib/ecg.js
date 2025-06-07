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
        const ecgData = {
            patientID: patientIDString,
            ipfsHash,
            timestamp,
            metadata: parsedMetadata,
            status: "PENDING_VERIFICATION",      // 🔒 Escrow: Start with PENDING
            accessControl: {
                owner: patientOwnerClientID,      // Patient sebagai owner
                authorizedUsers: []              // Awalnya kosong
            },
            accessHistory: [],
            inputBy: inputByClientID,             // Doctor yang input data
            createdAt: new Date().toISOString(),
            lastStatusUpdate: new Date().toISOString()
        };

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`ECG data stored with PENDING status for patient ${patientIDString} with owner ${patientOwnerClientID}, input by ${inputByClientID}`);
        
        // 🚨 EMIT EVENT untuk notification system
        const eventPayload = {
            eventType: 'ECG_DATA_STORED',
            patientID: patientIDString,
            ipfsHash: ipfsHash,
            timestamp: timestamp,
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
            timestamp: timestamp,
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

        // Update status based on verification result
        const newStatus = (isValid === 'true' || isValid === true) ? "CONFIRMED" : "FAILED";
        ecgData.status = newStatus;
        ecgData.lastStatusUpdate = new Date().toISOString();
        ecgData.verificationDetails = {
            verifiedBy: verifierClientID,
            verifiedAt: new Date().toISOString(),
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
            timestamp: new Date().toISOString(),
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

        // Validasi doctor client ID format
        if (!doctorClientIDToGrant || typeof doctorClientIDToGrant !== 'string' || !doctorClientIDToGrant.startsWith('x509::')) {
            throw new Error('Invalid doctorClientIDToGrant format. Expected full X.509 client ID string.');
        }
        
        if (!ecgData.accessControl.authorizedUsers.includes(doctorClientIDToGrant)) {
            ecgData.accessControl.authorizedUsers.push(doctorClientIDToGrant);
            console.info(`Access granted to ${doctorClientIDToGrant} for patient ${patientIDString} by owner ${callerClientID}`);

            // 🚨 EMIT EVENT untuk access granted notification
            const eventPayload = {
                eventType: 'ACCESS_GRANTED',
                patientID: patientIDString,
                grantedTo: doctorClientIDToGrant,
                grantedBy: callerClientID,
                timestamp: new Date().toISOString(),
                dataStatus: ecgData.status,
                notificationMessage: `Access granted to doctor for verified patient ${patientIDString} data`
            };

            ctx.stub.setEvent('AccessGranted', Buffer.from(JSON.stringify(eventPayload)));
            console.info(`Event emitted: AccessGranted for patient ${patientIDString} to ${doctorClientIDToGrant}`);
        } else {
            console.info(`${doctorClientIDToGrant} already has access to patient ${patientIDString}`);
        }

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ 
            status: 'success', 
            message: `Access granted to ${doctorClientIDToGrant} for patient ${patientIDString}`,
            dataStatus: ecgData.status
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

        // Validasi doctor client ID format
        if (!doctorClientIDToRevoke || typeof doctorClientIDToRevoke !== 'string' || !doctorClientIDToRevoke.startsWith('x509::')) {
            throw new Error('Invalid doctorClientIDToRevoke format. Expected full X.509 client ID string.');
        }

        const initialLength = ecgData.accessControl.authorizedUsers.length;
        ecgData.accessControl.authorizedUsers = ecgData.accessControl.authorizedUsers.filter(userClientID => userClientID !== doctorClientIDToRevoke);

        if (ecgData.accessControl.authorizedUsers.length < initialLength) {
            console.info(`Access revoked for ${doctorClientIDToRevoke} from patient ${patientIDString} by owner ${callerClientID}`);

            // 🚨 EMIT EVENT untuk access revoked notification
            const eventPayload = {
                eventType: 'ACCESS_REVOKED',
                patientID: patientIDString,
                revokedFrom: doctorClientIDToRevoke,
                revokedBy: callerClientID,
                timestamp: new Date().toISOString(),
                dataStatus: ecgData.status,
                notificationMessage: `Access revoked from doctor for patient ${patientIDString} data`
            };

            ctx.stub.setEvent('AccessRevoked', Buffer.from(JSON.stringify(eventPayload)));
            console.info(`Event emitted: AccessRevoked for patient ${patientIDString} from ${doctorClientIDToRevoke}`);
        } else {
            console.info(`${doctorClientIDToRevoke} was not found in authorized users for patient ${patientIDString}. No access revoked.`);
        }
        
        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ 
            status: 'success', 
            message: `Access revoked for ${doctorClientIDToRevoke} from patient ${patientIDString}`,
            dataStatus: ecgData.status
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

        // 🔒 ESCROW CHECK: Only allow access to CONFIRMED data
        if (ecgData.status !== "CONFIRMED") {
            throw new Error(`ECG data for patient ${patientIDString} is not yet confirmed. Current status: ${ecgData.status}. Access denied until verification is complete.`);
        }

        // Periksa apakah pemanggil adalah owner (patient) ATAU ada di daftar authorizedUsers
        if (accessorClientID !== ecgData.accessControl.owner && !ecgData.accessControl.authorizedUsers.includes(accessorClientID)) {
            console.error(`Unauthorized access attempt: Accessor ${accessorClientID} is not owner and not in authorized list for patient ${patientIDString}`);
            throw new Error(`Access denied. Only the patient owner or authorized doctors can access this data. Owner: ${ecgData.accessControl.owner}`);
        }

        const accessRecord = {
            accessorID: accessorClientID,
            timestamp: new Date().toISOString(),
            action: 'access_data',
            dataStatus: ecgData.status
        };
        ecgData.accessHistory.push(accessRecord);
        console.info(`Access recorded for ${accessorClientID} to patient ${patientIDString} (status: ${ecgData.status})`);

        // 🚨 EMIT EVENT untuk data access notification
        const eventPayload = {
            eventType: 'ECG_DATA_ACCESSED',
            patientID: patientIDString,
            accessedBy: accessorClientID,
            timestamp: accessRecord.timestamp,
            dataStatus: ecgData.status,
            notificationMessage: `Verified ECG data for patient ${patientIDString} was accessed by ${accessorClientID}`
        };

        ctx.stub.setEvent('ECGDataAccessed', Buffer.from(JSON.stringify(eventPayload)));
        console.info(`Event emitted: ECGDataAccessed for patient ${patientIDString} by ${accessorClientID}`);

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));

        // Return data yang relevan (tidak termasuk access control details untuk security)
        return JSON.stringify({
            patientID: ecgData.patientID,
            ipfsHash: ecgData.ipfsHash,
            timestamp: ecgData.timestamp,
            metadata: ecgData.metadata,
            status: ecgData.status,
            verificationDetails: ecgData.verificationDetails,
            accessGranted: true, 
            accessorInfo: { 
                id: accessorClientID, 
                accessTime: accessRecord.timestamp 
            }
        });
    }

    async getECGDataStatus(ctx, patientIDString) {
        console.info('========= Get ECG Data Status =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const callerClientID = this.getClientIdentityString(ctx);

        // Allow status check by owner or authorized users
        if (callerClientID !== ecgData.accessControl.owner && !ecgData.accessControl.authorizedUsers.includes(callerClientID)) {
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
