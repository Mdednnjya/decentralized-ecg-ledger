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

    async storeECGData(ctx, patientIDString, ipfsHash, timestamp, metadata) {
        console.info('========= Store ECG Data =========');

        // Pemanggil fungsi ini dianggap sebagai pemilik data (pasien)
        const ownerClientID = this.getClientIdentityString(ctx);

        const ecgData = {
            patientID: patientIDString, // ID pasien yang bisa dibaca manusia
            ipfsHash,
            timestamp,
            metadata: JSON.parse(metadata || '{}'),
            accessControl: {
                owner: ownerClientID,       // Simpan ID Kriptografi Pemilik
                authorizedUsers: []       // Awalnya kosong, pemilik otomatis bisa akses
            },
            accessHistory: []
        };

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));
        console.info(`ECG data stored for patient ${patientIDString} with owner ${ownerClientID}`);
        return JSON.stringify({ status: 'success', message: 'ECG data stored successfully', patientID: patientIDString, owner: ownerClientID });
    }

    async grantAccess(ctx, patientIDString, doctorClientIDToGrant) { // doctorClientIDToGrant harus ID X.509 lengkap
        console.info('========= Grant Access =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const callerClientID = this.getClientIdentityString(ctx);

        // Hanya pemilik data yang bisa memberikan akses
        if (callerClientID !== ecgData.accessControl.owner) {
            console.error(`Unauthorized grant attempt: Caller ${callerClientID} is not owner ${ecgData.accessControl.owner} of patient ${patientIDString}`);
            throw new Error(`Caller (${callerClientID}) is not the owner of patient data ${patientIDString}. Only the owner (${ecgData.accessControl.owner}) can grant access.`);
        }

        // Pastikan doctorClientIDToGrant adalah string X.509 yang valid (minimal tidak kosong)
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
        return JSON.stringify({ status: 'success', message: `Access granted to ${doctorClientIDToGrant} for patient ${patientIDString}` });
    }

    async revokeAccess(ctx, patientIDString, doctorClientIDToRevoke) { // doctorClientIDToRevoke harus ID X.509 lengkap
        console.info('========= Revoke Access =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const callerClientID = this.getClientIdentityString(ctx);

        // Hanya pemilik data yang bisa mencabut akses
        if (callerClientID !== ecgData.accessControl.owner) {
            console.error(`Unauthorized revoke attempt: Caller ${callerClientID} is not owner ${ecgData.accessControl.owner} of patient ${patientIDString}`);
            throw new Error(`Caller (${callerClientID}) is not the owner of patient data ${patientIDString}. Only the owner (${ecgData.accessControl.owner}) can revoke access.`);
        }

        // Pastikan doctorClientIDToRevoke adalah string X.509 yang valid
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
        return JSON.stringify({ status: 'success', message: `Access revoked for ${doctorClientIDToRevoke} from patient ${patientIDString}` });
    }

    async accessECGData(ctx, patientIDString) {
        console.info('========= Access ECG Data =========');

        const ecgDataBuffer = await ctx.stub.getState(patientIDString);
        if (!ecgDataBuffer || ecgDataBuffer.length === 0) {
            throw new Error(`Patient data for ${patientIDString} not found`);
        }

        const ecgData = JSON.parse(ecgDataBuffer.toString());
        const accessorClientID = this.getClientIdentityString(ctx);

        // Periksa apakah pemanggil adalah pemilik ATAU ada di daftar authorizedUsers
        if (accessorClientID !== ecgData.accessControl.owner && !ecgData.accessControl.authorizedUsers.includes(accessorClientID)) {
            console.error(`Unauthorized access attempt: Accessor ${accessorClientID} is not owner and not in authorized list for patient ${patientIDString}`);
            throw new Error(`Accessor (${accessorClientID}) is not authorized to access patient data ${patientIDString}. Owner: ${ecgData.accessControl.owner}, Authorized: ${ecgData.accessControl.authorizedUsers.join(', ')}`);
        }

        const accessRecord = {
            accessorID: accessorClientID,
            timestamp: new Date().toISOString() // Gunakan timestamp server, bukan dari klien
        };
        ecgData.accessHistory.push(accessRecord);
        console.info(`Access recorded for ${accessorClientID} to patient ${patientIDString}`);

        await ctx.stub.putState(patientIDString, Buffer.from(JSON.stringify(ecgData)));

        // Hanya kembalikan data yang relevan, bukan seluruh objek ecgData termasuk accessControl
        return JSON.stringify({
            patientID: ecgData.patientID,
            ipfsHash: ecgData.ipfsHash,
            timestamp: ecgData.timestamp,
            metadata: ecgData.metadata,
            // Untuk konfirmasi di klien, kita bisa tambahkan ini, tapi mungkin tidak untuk data sensitif
            accessGranted: true, 
            accessorInfo: { id: accessorClientID, accessTime: accessRecord.timestamp }
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

        // Hanya pemilik yang bisa melihat audit trail lengkap
        if (accessorClientID !== ecgData.accessControl.owner) {
            console.error(`Unauthorized audit trail access attempt: Accessor ${accessorClientID} is not owner ${ecgData.accessControl.owner} for patient ${patientIDString}`);
            throw new Error('Only the owner can view the audit trail');
        }
        console.info(`Audit trail accessed by owner ${accessorClientID} for patient ${patientIDString}`);
        return JSON.stringify(ecgData.accessHistory);
    }

    // Di dalam class ECGContract Anda:
    async getMyIdentity(ctx) {
    	const clientID = ctx.clientIdentity.getID();
    	console.info(`Client ID requesting is: ${clientID}`);
    	return clientID;
    }
}

module.exports = ECGContract;
