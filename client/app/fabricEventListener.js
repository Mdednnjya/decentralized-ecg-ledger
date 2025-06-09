/*
 * Hyperledger Fabric ECG Event Listener
 * This service listens to blockchain events and triggers alerts
 */

const { Gateway, Wallets } = require('fabric-network');
const path = require('path');
const fs = require('fs');

class ECGEventListener {
    constructor() {
        this.gateway = null;
        this.network = null;
        this.contract = null;
        this.isListening = false;
    }

    async connectToFabric() {
        try {
            // Load connection profile
            const ccpPath = path.resolve(__dirname, '..', 'config', 'connection-org1.json');
            const ccp = JSON.parse(fs.readFileSync(ccpPath, 'utf8'));

            // Create wallet (in production, load actual wallet)
            const wallet = await Wallets.newInMemoryWallet();
            
            // Connect to gateway
            this.gateway = new Gateway();
            await this.gateway.connect(ccp, {
                wallet,
                identity: 'appUser', // In production, use actual user identity
                discovery: { enabled: true, asLocalhost: false }
            });

            // Get network and contract
            this.network = await this.gateway.getNetwork('ecgchannel');
            this.contract = this.network.getContract('ecgcontract');

            console.log('✅ Connected to Hyperledger Fabric network');
            return true;
        } catch (error) {
            console.error('❌ Failed to connect to Fabric network:', error.message);
            return false;
        }
    }

    async startEventListening() {
        if (!this.network) {
            console.error('❌ Not connected to network. Call connectToFabric() first.');
            return;
        }

        try {
            console.log('🔄 Starting ECG event listeners...');

            // Listen to ECGDataStored events
            await this.network.addContractListener(
                'ecgcontract',
                'ECGDataStored',
                (event) => this.handleECGDataStoredEvent(event),
                (error) => console.error('❌ ECGDataStored listener error:', error)
            );

            // Listen to AccessGranted events  
            await this.network.addContractListener(
                'ecgcontract',
                'AccessGranted',
                (event) => this.handleAccessGrantedEvent(event),
                (error) => console.error('❌ AccessGranted listener error:', error)
            );

            // Listen to AccessRevoked events
            await this.network.addContractListener(
                'ecgcontract',
                'AccessRevoked', 
                (event) => this.handleAccessRevokedEvent(event),
                (error) => console.error('❌ AccessRevoked listener error:', error)
            );

            // Listen to ECGDataAccessed events
            await this.network.addContractListener(
                'ecgcontract',
                'ECGDataAccessed',
                (event) => this.handleECGDataAccessedEvent(event),
                (error) => console.error('❌ ECGDataAccessed listener error:', error)
            );

            this.isListening = true;
            console.log('✅ All event listeners started successfully');
            console.log('📡 Monitoring blockchain for ECG-related events...\n');

        } catch (error) {
            console.error('❌ Error starting event listeners:', error);
        }
    }

    handleECGDataStoredEvent(event) {
        try {
            const eventData = JSON.parse(event.payload.toString());
            const timestamp = new Date().toISOString();
            
            console.log('\n🚨 NEW ECG DATA ALERT 🚨');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`📋 Patient ID: ${eventData.patientID}`);
            console.log(`🏥 Hospital: ${eventData.hospital}`);
            console.log(`👨‍⚕️ Doctor: ${eventData.doctor}`);
            console.log(`⏰ Timestamp: ${eventData.timestamp}`);
            console.log(`🔗 IPFS Hash: ${eventData.ipfsHash.substring(0, 20)}...`);
            console.log(`📝 Input By: ${this.formatIdentity(eventData.inputBy)}`);
            console.log(`👤 Owner: ${this.formatIdentity(eventData.owner)}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

            // Log to file
            this.logAlert('ECG_DATA_STORED', eventData);

        } catch (error) {
            console.error('❌ Error processing ECGDataStored event:', error);
        }
    }

    handleAccessGrantedEvent(event) {
        try {
            const eventData = JSON.parse(event.payload.toString());
            
            console.log('\n🔓 ACCESS GRANTED ALERT');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`📋 Patient ID: ${eventData.patientID}`);
            console.log(`✅ Access granted to: ${this.formatIdentity(eventData.grantedTo)}`);
            console.log(`👤 Granted by: ${this.formatIdentity(eventData.grantedBy)}`);
            console.log(`⏰ Timestamp: ${eventData.timestamp}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

            this.logAlert('ACCESS_GRANTED', eventData);

        } catch (error) {
            console.error('❌ Error processing AccessGranted event:', error);
        }
    }

    handleAccessRevokedEvent(event) {
        try {
            const eventData = JSON.parse(event.payload.toString());
            
            console.log('\n🔒 ACCESS REVOKED ALERT');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`📋 Patient ID: ${eventData.patientID}`);
            console.log(`❌ Access revoked from: ${this.formatIdentity(eventData.revokedFrom)}`);
            console.log(`👤 Revoked by: ${this.formatIdentity(eventData.revokedBy)}`);
            console.log(`⏰ Timestamp: ${eventData.timestamp}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

            this.logAlert('ACCESS_REVOKED', eventData);

        } catch (error) {
            console.error('❌ Error processing AccessRevoked event:', error);
        }
    }

    handleECGDataAccessedEvent(event) {
        try {
            const eventData = JSON.parse(event.payload.toString());
            
            console.log('\n📋 DATA ACCESS ALERT');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`📋 Patient ID: ${eventData.patientID}`);
            console.log(`👀 Accessed by: ${this.formatIdentity(eventData.accessedBy)}`);
            console.log(`⏰ Timestamp: ${eventData.timestamp}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

            this.logAlert('ECG_DATA_ACCESSED', eventData);

        } catch (error) {
            console.error('❌ Error processing ECGDataAccessed event:', error);
        }
    }

    formatIdentity(identityString) {
        // Extract readable name from X.509 identity string
        if (identityString && identityString.includes('CN=')) {
            const cn = identityString.split('CN=')[1].split(',')[0].split('::')[0];
            return cn;
        }
        return identityString || 'Unknown';
    }

    logAlert(eventType, eventData) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            eventType: eventType,
            data: eventData
        };

        const logFile = '/tmp/ecg_events.log';
        const logLine = JSON.stringify(logEntry) + '\n';
        
        fs.appendFileSync(logFile, logLine);
    }

    async disconnect() {
        if (this.gateway) {
            await this.gateway.disconnect();
            console.log('🔌 Disconnected from Fabric network');
        }
    }
}

// Main execution
async function main() {
    const listener = new ECGEventListener();
    
    console.log('🚀 Starting ECG Blockchain Event Listener Service...');
    
    // Connect to Fabric network
    const connected = await listener.connectToFabric();
    if (!connected) {
        console.error('❌ Failed to connect to blockchain network');
        process.exit(1);
    }

    // Start event listening
    await listener.startEventListening();

    // Handle graceful shutdown
    process.on('SIGINT', async () => {
        console.log('\n🛑 Shutting down event listener...');
        await listener.disconnect();
        process.exit(0);
    });

    // Keep the service running
    console.log('🔄 ECG Alert Service is running. Press Ctrl+C to stop.\n');
}

// Export for use as module
module.exports = ECGEventListener;

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}
