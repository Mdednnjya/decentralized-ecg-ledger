import ipfshttpclient
import json
import os


class IPFSClient:
    def __init__(self, ipfs_host='127.0.0.1', ipfs_port=5001):
        self.client = ipfshttpclient.connect(f'/ip4/{ipfs_host}/tcp/{ipfs_port}')

    def upload_ecg_data(self, ecg_data):
        """
        Upload ECG data to IPFS

        Args:
            ecg_data (dict): ECG data in JSON format

        Returns:
            str: IPFS hash of the uploaded data
        """
        # Convert ECG data to JSON string
        ecg_json = json.dumps(ecg_data)

        # Add data to IPFS
        res = self.client.add_str(ecg_json)

        return res

    def get_ecg_data(self, ipfs_hash):
        """
        Retrieve ECG data from IPFS

        Args:
            ipfs_hash (str): IPFS hash of the ECG data

        Returns:
            dict: ECG data as a dictionary
        """
        # Get data from IPFS
        data = self.client.cat(ipfs_hash).decode('utf-8')

        # Parse JSON data
        ecg_data = json.loads(data)

        return ecg_data