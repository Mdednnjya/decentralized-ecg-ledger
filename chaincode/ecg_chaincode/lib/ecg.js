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
        console.info('========= Store ECG Data =========');

        // Doctor yang input data
        const inputByClientID = this.getClientIdentityString(ctx);

        // Patient yang menjadi owner data
        if (!patientOwnerClientID || patientOwnerClientID.trim() === '') {
            throw new Error('Patient owner client ID is required');
        }

        const ecgData = {
            patientID: patientIDString,
            ipfsHash,
            timestamp,
            metadata: JSON.parse(metadata || '{}'),
            accessControl: {
                owner: patientOwnerClientID,      // Patient sebagai owner
                authorizedUsers: []              // Awalnya kosong
            },
            accessHistory: [],
            inputBy: inputByClientID             // Doctor yang input data
        };

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`ECG data stored for patient ${patientIDString} with owner ${patientOwnerClientID}, input by ${inputByClientID}`);
        
        return JSON.stringify({ 
            status: 'success', 
            message: 'ECG data stored successfully', 
            patientID: patientIDString, 
            owner: patientOwnerClientID,
            inputBy: inputByClientID
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
        } else {
            console.info(`${doctorClientIDToGrant} already has access to patient ${patientIDString}`);
        }

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ 
            status: 'success', 
            message: `Access granted to ${doctorClientIDToGrant} for patient ${patientIDString}` 
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
        } else {
            console.info(`${doctorClientIDToRevoke} was not found in authorized users for patient ${patientIDString}. No access revoked.`);
        }
        
        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ 
            status: 'success', 
            message: `Access revoked for ${doctorClientIDToRevoke} from patient ${patientIDString}` 
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

        // Periksa apakah pemanggil adalah owner (patient) ATAU ada di daftar authorizedUsers
        if (accessorClientID !== ecgData.accessControl.owner && !ecgData.accessControl.authorizedUsers.includes(accessorClientID)) {
            console.error(`Unauthorized access attempt: Accessor ${accessorClientID} is not owner and not in authorized list for patient ${patientIDString}`);
            throw new Error(`Access denied. Only the patient owner or authorized doctors can access this data. Owner: ${ecgData.accessControl.owner}`);
        }

        const accessRecord = {
            accessorID: accessorClientID,
            timestamp: new Date().toISOString(),
            action: 'access_data'
        };
        ecgData.accessHistory.push(accessRecord);
        console.info(`Access recorded for ${accessorClientID} to patient ${patientIDString}`);

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));

        // Return data yang relevan (tidak termasuk access control details untuk security)
        return JSON.stringify({
            patientID: ecgData.patientID,
            ipfsHash: ecgData.ipfsHash,
            timestamp: ecgData.timestamp,
            metadata: ecgData.metadata,
            accessGranted: true, 
            accessorInfo: { 
                id: accessorClientID, 
                accessTime: accessRecord.timestamp 
            }
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
            auditTrail: ecgData.accessHistory,
            currentAuthorizedUsers: ecgData.accessControl.authorizedUsers,
            dataInputBy: ecgData.inputBy,
            owner: ecgData.accessControl.owner
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
