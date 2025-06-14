import paramiko
import json
import time
import re
import datetime
import requests
import random
from typing import Dict, Tuple, Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()

PEER0_ORG1_UNAME = os.getenv("PEER0_ORG1_UNAME")
PEER0_ORG1_PASSW = os.getenv("PEER0_ORG1_PASSW")
PEER1_ORG1_UNAME = os.getenv("PEER1_ORG1_UNAME")
PEER1_ORG1_PASSW = os.getenv("PEER1_ORG1_PASSW")
PEER0_ORG2_UNAME = os.getenv("PEER0_ORG2_UNAME")
PEER0_ORG2_PASSW = os.getenv("PEER0_ORG2_PASSW")
PEER1_ORG2_UNAME = os.getenv("PEER1_ORG2_UNAME")
PEER1_ORG2_PASSW = os.getenv("PEER1_ORG2_PASSW")

# --- Configuration for Peer VMs (for getinfo) ---
PEERS_CONFIG = [
    {
        "name": "Peer0.Org1",
        "host": "10.34.100.126",
        "username": PEER0_ORG1_UNAME,
        "password": PEER0_ORG1_PASSW,
        "peer_container_name": "peer0.org1.example.com",
    },
    {
        "name": "Peer1.Org1",
        "host": "10.34.100.128",
        "username": PEER1_ORG1_UNAME,
        "password": PEER1_ORG1_PASSW,
        "peer_container_name": "peer1.org1.example.com",
    },
    {
        "name": "Peer0.Org2",
        "host": "10.34.100.114",
        "username": PEER0_ORG2_UNAME,
        "password": PEER0_ORG2_PASSW,
        "peer_container_name": "peer0.org2.example.com",
    },
    {
        "name": "Peer1.Org2",
        "host": "10.34.100.116",
        "username": PEER1_ORG2_UNAME,
        "password": PEER1_ORG2_PASSW,
        "peer_container_name": "peer1.org2.example.com",
    },
]

CHANNEL_NAME = "ecgchannel"

# --- Configuration for Transaction Invocation via API ---
API_ENDPOINT_CONFIG = {
    "url": "http://10.34.100.125:3000/ecg/upload",
    "headers": {
        "X-User-Role": "admin",
    },
}

# Test parameters
POLL_INTERVAL_SECONDS = 1
SYNCHRONIZATION_TIMEOUT_SECONDS = 120  # Increased timeout for potentially larger data


# --- SSH Helper Function (for getinfo) ---
def execute_ssh_command(
    host: str, username: str, password: str, command: str
) -> Tuple[Optional[str], Optional[str]]:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            host,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False,
        )
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        output = stdout.read().decode("utf-8").strip()
        error = stderr.read().decode("utf-8").strip()
        return output, error
    except paramiko.AuthenticationException:
        print(f"Authentication failed for {username}@{host}. Please check password.")
        return None, f"Authentication failed for {username}@{host}"
    except Exception as e:
        print(f"SSH Error connecting to {username}@{host} or executing command: {e}")
        return None, str(e)
    finally:
        client.close()


# --- Fabric Helper Functions (for getinfo) ---
def parse_getinfo_output(output: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"Blockchain info: ({.*})", output)
    if match:
        try:
            json_str = match.group(1)
            data = json.loads(json_str)
            return {
                "height": int(data.get("height", 0)),
                "currentBlockHash": data.get("currentBlockHash", ""),
                "previousBlockHash": data.get("previousBlockHash", ""),
            }
        except (json.JSONDecodeError, ValueError) as e:
            print(
                f"Error parsing JSON/int from getinfo output: {e}\nOutput was: {output}"
            )
            return None
    else:
        try:
            data = json.loads(output)
            return {
                "height": int(data.get("height", 0)),
                "currentBlockHash": data.get("currentBlockHash", ""),
                "previousBlockHash": data.get("previousBlockHash", ""),
            }
        except Exception:
            print(
                f"Could not find 'Blockchain info:' or parse raw output as JSON.\nOutput: {output}"
            )
            return None


def get_peer_ledger_info(
    peer_config: Dict[str, str], channel_name: str
) -> Optional[Dict[str, Any]]:
    command = f"docker exec {peer_config['peer_container_name']} peer channel getinfo -c {channel_name}"
    # print(f"Executing on {peer_config['name']} ({peer_config['host']}): {command}") # Less verbose polling
    stdout, stderr = execute_ssh_command(
        peer_config["host"], peer_config["username"], peer_config["password"], command
    )
    if stderr:
        # Suppress non-critical errors during polling unless debugging
        if (
            "error" in stderr.lower()
            or "failed" in stderr.lower()
            and "QueryCreator" not in stderr
        ):  # QueryCreator error can be ignored
            print(f"Stderr (getinfo from {peer_config['name']}): {stderr}")
    if stdout:
        return parse_getinfo_output(stdout)
    return None


# --- Payload Generation Function ---
def generate_api_payload(
    patient_id_str: str, num_lead_datapoints: int
) -> Dict[str, Any]:
    """
    Generates a dummy payload for the ECG API with variable lead data size.
    """
    # Use datetime.datetime.now(datetime.UTC) as recommended
    current_timestamp_iso = (
        datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    )

    leads_data = {}
    # Simulate a few common ECG leads
    lead_names = ["I", "II", "V1", "V2", "V5", "V6"]

    for lead_name in lead_names:
        # Generate 'num_lead_datapoints' random float values (e.g., between -2.0 and 2.0 mV)
        # Using simple integer sequences for this test to reduce randomness impact on size/speed,
        # but random floats are more realistic for actual data.
        # leads_data[lead_name] = [round(random.uniform(-2.0, 2.0), 3) for _ in range(num_lead_datapoints)]
        leads_data[lead_name] = [i * 0.001 for i in range(num_lead_datapoints)]

    ecg_data_content = {
        "patientInfo": {
            "id": patient_id_str,
            "age": random.randint(20, 80),
            "gender": random.choice(["M", "F", "O"]),
            "symptoms": f"Test symptoms for payload with {num_lead_datapoints} lead data points.",
        },
        "recordInfo": {
            "deviceId": f"ECG-TEST-{num_lead_datapoints}pts",
            "timestamp": current_timestamp_iso,
            "samplingRate": 500,
        },
        "leads": leads_data,
        "analysis": {
            "heartRate": random.randint(50, 120),
            "rhythm": random.choice(
                ["Normal Sinus Rhythm", "Atrial Fibrillation", "Sinus Tachycardia"]
            ),
            "intervals": {
                "PR": random.randint(120, 200),
                "QRS": random.randint(70, 110),
                "QT": random.randint(350, 440),
            },
            "notes": f"Automated analysis for {num_lead_datapoints} lead data points.",
        },
    }

    metadata_content = {
        "hospital": f"Test Hospital (Data Size: {num_lead_datapoints} pts)",
        "doctor": f"Dr. Test {random.randint(1,10)}",
        "department": "Cardiology Test Department",
    }

    payload = {
        "patientId": patient_id_str,
        "ecgData": ecg_data_content,
        "metadata": metadata_content,
    }
    return payload


# --- Transaction Invocation Helper (via API) ---
def invoke_transaction_via_api(
    api_config: Dict[str, Any], num_lead_datapoints: int
) -> bool:
    """Invokes a transaction by sending a POST request to the API with specified data size."""
    # Make patientId unique for each run/invocation to ensure new data
    unique_patient_id = (
        f"PEERGROUP-PATIENT-TEST{int(time.time())}-{num_lead_datapoints}"
    )

    payload = generate_api_payload(unique_patient_id, num_lead_datapoints)

    print(f"\nAttempting to invoke transaction via API: POST to {api_config['url']}")
    print(
        f"Payload for patientId: {unique_patient_id}, Lead data points per lead: {num_lead_datapoints}"
    )
    # To see the full payload for debugging (can be very large):
    # print(f"Full Payload: {json.dumps(payload, indent=2)}")

    try:
        start_api_call_time = time.time()
        response = requests.post(
            api_config["url"],
            headers=api_config["headers"],
            json=payload,
            timeout=60,  # Increased timeout for potentially large payloads
        )
        api_call_duration = time.time() - start_api_call_time
        print(
            f"API Response Status Code: {response.status_code} (took {api_call_duration:.2f}s)"
        )

        try:
            response_json = response.json()
            # print(f"API Response Body: {json.dumps(response_json, indent=2)}") # Can be verbose
        except requests.exceptions.JSONDecodeError:
            print(f"API Response Body (not JSON): {response.text[:200]}...")

        if 200 <= response.status_code < 300:
            print("Transaction invocation via API appears SUCCESSFUL.")
            return True
        else:
            print(
                f"Transaction invocation via API FAILED. Status: {response.status_code}"
            )
            return False

    except requests.exceptions.Timeout:
        print(
            f"Error invoking transaction via API: Request timed out to {api_config['url']}"
        )
        return False
    except requests.exceptions.ConnectionError:
        print(
            f"Error invoking transaction via API: Connection refused or DNS failure for {api_config['url']}"
        )
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error invoking transaction via API: {e}")
        return False


# --- Main Test Logic ---
def run_sync_test(num_lead_datapoints_for_test: int):
    print(
        f"--- Ledger Synchronization Test (Lead Data Points: {num_lead_datapoints_for_test}) ---"
    )

    # 1. Get initial state
    print("\n--- Getting initial ledger state ---")
    initial_peer_info = None
    for peer_conf in PEERS_CONFIG:  # Try all peers until one gives info
        initial_peer_info = get_peer_ledger_info(peer_conf, CHANNEL_NAME)
        if initial_peer_info and initial_peer_info.get("height") is not None:
            print(
                f"Initial state from {peer_conf['name']}: Height {initial_peer_info['height']}"
            )
            break
        else:
            print(
                f"Could not get initial state from {peer_conf['name']}. Trying next..."
            )

    if not initial_peer_info or initial_peer_info.get("height") is None:
        print(
            "CRITICAL: Could not determine initial ledger height from any peer. Aborting test for this size."
        )
        return

    initial_height = initial_peer_info["height"]
    target_height = initial_height + 1
    print(
        f"Initial height: {initial_height}. Target height after transaction: {target_height}"
    )

    # 2. Invoke Transaction via API
    print("\n--- Invoking Transaction via API ---")
    if not invoke_transaction_via_api(
        API_ENDPOINT_CONFIG, num_lead_datapoints_for_test
    ):
        print(
            "Transaction invocation via API failed. Aborting synchronization test for this size."
        )
        return

    print("Transaction submitted. Waiting a moment for initial propagation...")
    time.sleep(1)
    # time.sleep(3 + num_lead_datapoints_for_test // 1000)

    # 3. Poll peers for synchronization
    print(f"\n--- Checking for Synchronization (Target Height: {target_height}) ---")
    start_time_sync_check = time.time()
    sync_achieved_time = None
    all_synced = False

    target_block_hash = None
    target_prev_block_hash = None
    current_peer_states: Dict[str, Optional[Dict[str, Any]]] = {
        p["name"]: None for p in PEERS_CONFIG
    }

    max_poll_attempts = int(SYNCHRONIZATION_TIMEOUT_SECONDS / POLL_INTERVAL_SECONDS)
    for i in range(max_poll_attempts):
        if (i + 1) % 1 == 0 or i == 0:
            print(
                f"\n--- Poll attempt {i+1}/{max_poll_attempts} (Elapsed: {time.time() - start_time_sync_check:.1f}s) ---"
            )

        all_match_target_state_this_poll = True
        peers_at_target_height_count = 0

        for peer_conf in PEERS_CONFIG:
            info = get_peer_ledger_info(peer_conf, CHANNEL_NAME)
            current_peer_states[peer_conf["name"]] = info
            if info:
                if (i + 1) % 1 == 0 or i == 0:
                    print(
                        f"  {peer_conf['name']}: H={info['height']}, CH={info['currentBlockHash'][:8]}..., PH={info['previousBlockHash'][:8]}..."
                    )

                if info["height"] == target_height:
                    peers_at_target_height_count += 1
                    if target_block_hash is None:
                        target_block_hash = info["currentBlockHash"]
                        target_prev_block_hash = info["previousBlockHash"]
                        if (i + 1) % 1 == 0 or i == 0:  # Print only on selected polls
                            print(
                                f"  INFO: {peer_conf['name']} reached target H={target_height}. Set target hashes."
                            )

                if target_block_hash:
                    if not (
                        info["height"] == target_height
                        and info["currentBlockHash"] == target_block_hash
                        and info["previousBlockHash"] == target_prev_block_hash
                    ):
                        all_match_target_state_this_poll = False
                else:
                    all_match_target_state_this_poll = False
            else:
                if (i + 1) % 1 == 0 or i == 0:
                    print(
                        f"  WARN: {peer_conf['name']}: Could not retrieve info this poll."
                    )
                all_match_target_state_this_poll = False

        if (
            peers_at_target_height_count == len(PEERS_CONFIG)
            and target_block_hash is None
        ):
            for peer_conf_for_target in PEERS_CONFIG:
                info_for_target = current_peer_states[peer_conf_for_target["name"]]
                if info_for_target and info_for_target["height"] == target_height:
                    target_block_hash = info_for_target["currentBlockHash"]
                    target_prev_block_hash = info_for_target["previousBlockHash"]
                    if (i + 1) % 1 == 0 or i == 0:
                        print(
                            f"  INFO: All peers at H={target_height}. Set target hashes based on {peer_conf_for_target['name']}."
                        )
                    all_match_target_state_this_poll = True
                    for p_name_check, p_info_check in current_peer_states.items():
                        if not (
                            p_info_check
                            and p_info_check["height"] == target_height
                            and p_info_check["currentBlockHash"] == target_block_hash
                            and p_info_check["previousBlockHash"]
                            == target_prev_block_hash
                        ):
                            all_match_target_state_this_poll = False
                            break
                    break

        if all_match_target_state_this_poll and target_block_hash is not None:
            sync_achieved_time = time.time()
            all_synced = True
            print(
                f"\nSUCCESS: All {len(PEERS_CONFIG)} peers synchronized at Height {target_height}!"
            )
            break

        if (time.time() - start_time_sync_check) > SYNCHRONIZATION_TIMEOUT_SECONDS:
            print(
                f"\nTIMEOUT: Not all peers synchronized for {num_lead_datapoints_for_test} points within {SYNCHRONIZATION_TIMEOUT_SECONDS}s."
            )
            break

        time.sleep(POLL_INTERVAL_SECONDS)

    # 4. Report Results
    print(f"\n--- Test Results for {num_lead_datapoints_for_test} Lead Data Points ---")
    if all_synced and sync_achieved_time:
        propagation_time = sync_achieved_time - start_time_sync_check
        print(f"All peers synchronized to Height {target_height}.")
        print(
            f"Time to synchronization (after API call returned success): {propagation_time:.2f} seconds."
        )
        print(
            f"Final synchronized state: H={target_height}, CH={target_block_hash[:16]}..., PH={target_prev_block_hash[:16]}..."
        )
    else:
        print("Synchronization FAILED or timed out.")
        print("Last known states:")
        for peer_conf in PEERS_CONFIG:
            info = current_peer_states.get(peer_conf["name"])
            if info:
                print(
                    f"  {peer_conf['name']}: H={info['height']}, CH={info['currentBlockHash'][:16]}..., PH={info['previousBlockHash'][:16]}..."
                )
            else:
                print(f"  {peer_conf['name']}: No data / Error retrieving data.")
    print("-" * 50)


if __name__ == "__main__":
    # --- IMPORTANT ---
    # 1. Ensure `requests` and `paramiko` libraries are installed.
    # 2. Replace password fields in PEERS_CONFIG with actual passwords.
    # 3. Verify API_ENDPOINT_CONFIG (URL and headers).
    # 4. Ensure the machine running this script can reach the API endpoint (10.34.100.125:3000)
    #    and SSH into the peer VMs.

    # Define the sizes of lead data points to test
    # (Number of data points per lead, e.g., for "I", "II", etc.)
    # Be cautious with very large numbers (e.g., > 100,000) as it might strain the API/network/Fabric.
    # Total payload size = roughly (num_leads * num_datapoints_per_lead * avg_bytes_per_datapoint)
    # If 6 leads, 10000 points, each point is a float (e.g., 5-8 chars like "0.123,"), total could be ~300-500KB for leads.
    sizes_to_test = [
        100,
        1000,
        5000,
        10000,
    ]  # Number of data points per individual lead array

    for size in sizes_to_test:
        print(
            f"\n\n{'='*3} STARTING TEST RUN FOR {size} LEAD DATA POINTS PER LEAD {'='*3}"
        )
        run_sync_test(num_lead_datapoints_for_test=size)
        print(
            f"{'='*3} COMPLETED TEST RUN FOR {size} LEAD DATA POINTS PER LEAD {'='*3}"
        )
        if size != sizes_to_test[-1]:  # Don't sleep after the last test
            print(f"Pausing for 5 seconds before the next test size...")
            time.sleep(5)  # Pause between different test sizes
