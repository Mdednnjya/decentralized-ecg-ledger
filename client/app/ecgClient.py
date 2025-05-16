import os
import json
import datetime
from hfc.fabric import Client as FabricClient


class ECGClient:
    def __init__(self, channel_name, org_name, user_name, config_path):
        """
        Initialize the ECG client

        Args:
            channel_name (str): Name of the channel
            org_name (str): Name of the organization
            user_name (str): Name of the user
            config_path (str): Path to the connection profile
        """
        self.channel_name = channel_name
        self.org_name = org_name
        self.user_name = user_name

        # Initialize Fabric client
        self.client = FabricClient(net_profile=config_path)

        # Set up the client
        self._setup_client()

    def _setup_client(self):
        """Set up the Fabric client"""
        try:
            # Load the user from state store
            user = self.client.get_user(self.org_name, self.user_name)
        except:
            # User not found, enroll the user
            self._enroll_user()

    def _enroll_user(self):
        """Enroll a new user"""
        # For a real implementation, this would use the Fabric CA client to enroll a user
        # Simplified for this example
        pass

    async def store_ecg_data(self, patient_id, ipfs_hash, metadata=None):
        """
        Store ECG data on the blockchain

        Args:
            patient_id (str): ID of the patient
            ipfs_hash (str): IPFS hash of the ECG data
            metadata (dict): Additional metadata about the ECG

        Returns:
            dict: Response from the chaincode
        """
        # Set up the chaincode
        cc = self.client.get_channel(self.channel_name).get_chaincode('ecgcc')

        # Current timestamp
        timestamp = datetime.datetime.now().isoformat()

        # Convert metadata to JSON string
        metadata_str = json.dumps(metadata) if metadata else '{}'

        # Invoke the chaincode
        response = await cc.invoke(
            'storeECGData',
            [patient_id, ipfs_hash, timestamp, metadata_str],
            self.user_name
        )

        return json.loads(response)

    async def grant_access(self, patient_id, user_id):
        """
        Grant access to a user for a patient's ECG data

        Args:
            patient_id (str): ID of the patient
            user_id (str): ID of the user to grant access

        Returns:
            dict: Response from the chaincode
        """
        # Set up the chaincode
        cc = self.client.get_channel(self.channel_name).get_chaincode('ecgcc')

        # Invoke the chaincode
        response = await cc.invoke(
            'grantAccess',
            [patient_id, user_id],
            self.user_name
        )

        return json.loads(response)

    async def revoke_access(self, patient_id, user_id):
        """
        Revoke access from a user for a patient's ECG data

        Args:
            patient_id (str): ID of the patient
            user_id (str): ID of the user to revoke access

        Returns:
            dict: Response from the chaincode
        """
        # Set up the chaincode
        cc = self.client.get_channel(self.channel_name).get_chaincode('ecgcc')

        # Invoke the chaincode
        response = await cc.invoke(
            'revokeAccess',
            [patient_id, user_id],
            self.user_name
        )

        return json.loads(response)

    async def access_ecg_data(self, patient_id):
        """
        Access ECG data

        Args:
            patient_id (str): ID of the patient

        Returns:
            dict: ECG data information
        """
        # Set up the chaincode
        cc = self.client.get_channel(self.channel_name).get_chaincode('ecgcc')

        # Invoke the chaincode
        response = await cc.invoke(
            'accessECGData',
            [patient_id],
            self.user_name
        )

        return json.loads(response)

    async def get_audit_trail(self, patient_id):
        """
        Get the audit trail for a patient's ECG data

        Args:
            patient_id (str): ID of the patient

        Returns:
            list: Audit trail records
        """
        # Set up the chaincode
        cc = self.client.get_channel(self.channel_name).get_chaincode('ecgcc')

        # Invoke the chaincode
        response = await cc.invoke(
            'getAuditTrail',
            [patient_id],
            self.user_name
        )

        return json.loads(response)