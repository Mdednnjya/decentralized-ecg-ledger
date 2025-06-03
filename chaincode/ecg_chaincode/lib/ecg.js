'use strict';

const { Contract } = require('fabric-contract-api');

class ECGContract extends Contract {

    // Initialize the chaincode
    async initLedger(ctx) {
        console.info('========= ECG Chaincode Initialized =========');
        return;
    }

    // Store ECG data (only hash on-chain, actual data in IPFS)
    async storeECGData(ctx, patientID, ipfsHash, timestamp, metadata) {
        console.info('========= Store ECG Data =========');

        // Create ECG record
        const ecgData = {
            patientID,
            ipfsHash,
            timestamp,
            metadata: JSON.parse(metadata || '{}'),
            accessControl: {
                owner: patientID,
                authorizedUsers: [] // Initially only patient has access
            },
            accessHistory: []
        };

        await ctx.stub.putState(patientID, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ status: 'success', message: 'ECG data stored successfully' });
    }

    // Grant access to a specific user
    async grantAccess(ctx, patientID, userID) {
        console.info('========= Grant Access =========');

        // Get ECG data
        const ecgDataBuffer = await ctx.stub.getState(patientID);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient ${patientID} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());

        // Verify that transaction submitter is the owner
        const clientID = this.getClientID(ctx);
        if (clientID !== ecgData.accessControl.owner) {
            throw new Error('Only the owner can grant access');
        }

        // Add user to authorized list if not already there
        if (!ecgData.accessControl.authorizedUsers.includes(userID)) {
            ecgData.accessControl.authorizedUsers.push(userID);
        }

        // Update state
        await ctx.stub.putState(patientID, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ status: 'success', message: `Access granted to ${userID}` });
    }

    // Revoke access from a specific user
    async revokeAccess(ctx, patientID, userID) {
        console.info('========= Revoke Access =========');

        // Get ECG data
        const ecgDataBuffer = await ctx.stub.getState(patientID);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient ${patientID} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());

        // Verify that transaction submitter is the owner
        const clientID = this.getClientID(ctx);
        if (clientID !== ecgData.accessControl.owner) {
            throw new Error('Only the owner can revoke access');
        }

        // Remove user from authorized list
        ecgData.accessControl.authorizedUsers = ecgData.accessControl.authorizedUsers.filter(user => user !== userID);

        // Update state
        await ctx.stub.putState(patientID, Buffer.from(JSON.stringify(ecgData)));
        return JSON.stringify({ status: 'success', message: `Access revoked from ${userID}` });
    }

    // Access ECG data
    async accessECGData(ctx, patientID) {
        console.info('========= Access ECG Data =========');

        // Get ECG data
        const ecgDataBuffer = await ctx.stub.getState(patientID);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient ${patientID} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());

        // Get accessor ID
        const accessorID = this.getClientID(ctx);

        // Check if accessor is authorized
        if (accessorID !== ecgData.accessControl.owner && !ecgData.accessControl.authorizedUsers.includes(accessorID)) {
            throw new Error('Unauthorized access');
        }

        // Record access in history
        ecgData.accessHistory.push({
            accessorID,
            timestamp: new Date().toISOString()
        });

        // Update state with access record
        await ctx.stub.putState(patientID, Buffer.from(JSON.stringify(ecgData)));

        // Return IPFS hash and metadata
        return JSON.stringify({
            patientID: ecgData.patientID,
            ipfsHash: ecgData.ipfsHash,
            timestamp: ecgData.timestamp,
            metadata: ecgData.metadata
        });
    }

    // Get the audit trail for a patient's ECG data
    async getAuditTrail(ctx, patientID) {
        console.info('========= Get Audit Trail =========');

        // Get ECG data
        const ecgDataBuffer = await ctx.stub.getState(patientID);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient ${patientID} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());

        // Get accessor ID
        const accessorID = this.getClientID(ctx);

        // Check if accessor is authorized (only owner should see audit trail)
        if (accessorID !== ecgData.accessControl.owner) {
            throw new Error('Only the owner can view the audit trail');
        }

        return JSON.stringify(ecgData.accessHistory);
    }

    // Helper method to get the client ID from the transaction context
    getClientID(ctx) {
        // In a real implementation, you would extract the client ID from certificates
        // For simplicity, we'll use a mock ID here
        return ctx.clientIdentity.getID();
    }
}

module.exports = ECGContract;