import requests
import json
import time
import uuid 
import datetime
import random 

# --- Konfigurasi ---
API_BASE_URL = "http://10.34.100.125:3000"

# Endpoint untuk mengunggah data EKG (Admin role)
UPLOAD_ECG_ENDPOINT = f"{API_BASE_URL}/ecg/upload"

# Endpoint untuk memberikan izin akses (Patient role)
GRANT_ACCESS_ENDPOINT = f"{API_BASE_URL}/ecg/grant-access" 

# Endpoint untuk mengakses data EKG (Doctor role)
ACCESS_ECG_ENDPOINT = f"{API_BASE_URL}/ecg/access/" 

REQUEST_TIMEOUT = 20 # Timeout untuk request HTTP (dalam detik), diperpanjang sedikit
WAIT_TIME_AFTER_UPLOAD_FOR_CONFIRMATION = 15  
WAIT_TIME_AFTER_GRANT = 5 # Waktu tunggu setelah grant access sebelum akses

# --- Dummy User Roles ---
ADMIN_ROLE = "admin"
PATIENT_ROLE = "patient" 
DOCTOR_ROLE = "doctor"
TARGET_DOCTOR_ID = "DR-TEST-001" 

# --- Fungsi untuk Menyiapkan Data EKG Dummy ---
def generate_dummy_ecg_payload(group_number="5"):
    """
    Menghasilkan payload data EKG dummy sesuai format yang diberikan.
    """
    current_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'
    unique_patient_id = f"GROUP{group_number}-PATIENT{uuid.uuid4().hex[:5].upper()}"

    num_points = 100 
    leads_data = {
        "I": [round(random.uniform(-0.5, 1.0), 3) for _ in range(num_points)],
        "II": [round(random.uniform(-0.7, 1.2), 3) for _ in range(num_points)],
    }

    payload = {
        "patientId": unique_patient_id,
        "ecgData": {
            "patientInfo": {
                "id": unique_patient_id,
                "age": random.randint(20, 80),
                "gender": random.choice(["M", "F"]),
                "symptoms": random.choice(["chest pain", "shortness of breath", "palpitations", "none"])
            },
            "recordInfo": {
                "deviceId": f"ECG-{random.randint(100, 999)}",
                "timestamp": current_timestamp,
                "samplingRate": 500
            },
            "leads": leads_data,
            "analysis": {
                "heartRate": random.randint(60, 100),
                "rhythm": random.choice(["normal", "arrhythmia"])
            }
        },
        "metadata": {
            "hospital": "Rumah Sakit UMM", # Menggunakan contoh Anda
            "doctor": f"Dr. {random.choice(['Budi', 'Ani', 'Citra'])}",
            "department": "Jantung"
        }
    }
    return payload

# --- Fungsi Utama Pengujian End-to-End ---
def test_ecg_upload_grant_and_access():
    """
    Melakukan pengujian end-to-end:
    1. Admin mengunggah data EKG.
    2. Menunggu hingga data mungkin berstatus CONFIRMED secara internal.
    3. Pasien memberikan izin akses ke dokter.
    4. Dokter mencoba mengakses data.
    5. Memverifikasi data yang diakses.
    """
    print("--- Memulai Pengujian End-to-End Unggah, Tunggu Verifikasi, Beri Izin, & Akses Data EKG ---")

    # 1. Siapkan Data EKG Dummy
    dummy_payload = generate_dummy_ecg_payload()
    patient_id_to_test = dummy_payload["patientId"]
    print(f"Menggunakan Patient ID untuk Pengujian: {patient_id_to_test}")

    # 2. Unggah Data EKG sebagai Admin (POST Request)
    print(f"\n[STEP 1/4] Mengunggah data EKG sebagai {ADMIN_ROLE} ke: {UPLOAD_ECG_ENDPOINT}")
    upload_success = False
    try:
        headers = {"X-User-Role": ADMIN_ROLE, "Content-Type": "application/json"}
        response_upload = requests.post(UPLOAD_ECG_ENDPOINT, json=dummy_payload, headers=headers, timeout=REQUEST_TIMEOUT)
        response_upload.raise_for_status()

        upload_response_data = response_upload.json()
        print(f"Status Kode Respons Unggah: {response_upload.status_code}")
        print(f"Respons Unggah JSON: {json.dumps(upload_response_data, indent=2)}")

        if response_upload.status_code in [200, 201, 202] and upload_response_data.get("status") == "success":
            print(f">>> Unggah Data Berhasil untuk Patient ID: {patient_id_to_test} <<<")
            upload_success = True
        else:
            print("!!! Unggah Data GAGAL. Periksa respons dan log server. !!!")
            print(f"Detail Kegagalan: Status API '{upload_response_data.get('status')}', Pesan: '{upload_response_data.get('message')}'")


    except requests.exceptions.RequestException as e:
        print(f"ERROR: Gagal mengunggah data EKG ke {UPLOAD_ECG_ENDPOINT}.")
        print(f"Detail Error: {e}")
        upload_success = False
    except json.JSONDecodeError:
        print(f"ERROR: Respon unggah dari {UPLOAD_ECG_ENDPOINT} bukan JSON yang valid.")
        upload_success = False

    if not upload_success:
        print("Pengujian end-to-end dibatalkan karena unggah data gagal.")
        return

    # 3. Tunggu untuk Verifikasi Internal Data
    print(f"\n[STEP 2/4] Mengunggu {WAIT_TIME_AFTER_UPLOAD_FOR_CONFIRMATION} detik untuk verifikasi internal data (PENDING_VERIFICATION -> CONFIRMED)...")
    time.sleep(WAIT_TIME_AFTER_UPLOAD_FOR_CONFIRMATION)

    # 4. Berikan Izin Akses ke Dokter (POST Request)
    grant_payload = {
        "patientId": patient_id_to_test
        # Asumsi: authorizedUserId adalah default, atau ditangani di backend
        # Jika Anda perlu mengirim authorizedUserId, tambahkan di sini: "authorizedUserId": TARGET_DOCTOR_ID
    }
    print(f"\n[STEP 3/4] Memberikan izin akses sebagai {PATIENT_ROLE} untuk Patient ID: {patient_id_to_test}")
    print(f"Payload Izin: {json.dumps(grant_payload, indent=2)}")
    grant_success = False
    try:
        # Peran yang memberikan izin adalah "patient" sesuai contoh Anda
        grant_headers = {"X-User-Role": PATIENT_ROLE, "Content-Type": "application/json"} 
        response_grant = requests.post(GRANT_ACCESS_ENDPOINT, json=grant_payload, headers=grant_headers, timeout=REQUEST_TIMEOUT)
        response_grant.raise_for_status()

        grant_response_data = response_grant.json()
        print(f"Status Kode Respons Izin: {response_grant.status_code}")
        print(f"Respons Izin JSON: {json.dumps(grant_response_data, indent=2)}")

        # Verifikasi respons pemberian izin
        if response_grant.status_code in [200, 201, 202] and grant_response_data.get("status") == "success":
            print(f">>> Pemberian Izin Akses Berhasil untuk Patient ID: {patient_id_to_test} <<<")
            grant_success = True
        else:
            print("!!! Pemberian Izin Akses GAGAL. Periksa respons dan log server. !!!")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Gagal memberikan izin akses ke {GRANT_ACCESS_ENDPOINT}.")
        print(f"Detail Error: {e}")
        grant_success = False
    except json.JSONDecodeError:
        print(f"ERROR: Respon pemberian izin dari {GRANT_ACCESS_ENDPOINT} bukan JSON yang valid.")
        grant_success = False

    if not grant_success:
        print("Pengujian end-to-end dibatalkan karena pemberian izin akses gagal.")
        return

    # Tunggu sebentar setelah pemberian izin
    print(f"\nMengunggu {WAIT_TIME_AFTER_GRANT} detik setelah pemberian izin...")
    time.sleep(WAIT_TIME_AFTER_GRANT)

    # 5. Akses Data EKG sebagai Dokter (GET Request)
    access_url = f"{ACCESS_ECG_ENDPOINT}{patient_id_to_test}"
    print(f"\n[STEP 4/4] Mengakses data EKG sebagai {DOCTOR_ROLE} dari: {access_url}")
    access_success = False
    try:
        access_headers = {"X-User-Role": DOCTOR_ROLE}
        response_access = requests.get(access_url, headers=access_headers, timeout=REQUEST_TIMEOUT)
        response_access.raise_for_status()

        access_response_data = response_access.json()
        print(f"Status Kode Respons Akses: {response_access.status_code}")
        print(f"Respons Akses JSON: {json.dumps(access_response_data, indent=2)}")

        # 6. Verifikasi Data yang Diakses
        retrieved_main_data = access_response_data.get("data", {}) 
        retrieved_patient_id_from_data = retrieved_main_data.get("patientID") 

        if (access_response_data.get("patientId") == patient_id_to_test and  # patientId di level root
            retrieved_patient_id_from_data == patient_id_to_test and # patientID di dalam "data"
            retrieved_main_data.get("patientID") == patient_id_to_test and # patientID di dalam "data"
            retrieved_main_data.get("status") == "CONFIRMED" # Pastikan status data CONFIRMED
        ):
            print("\n>>> Verifikasi Data Berhasil: Data yang diakses cocok dengan yang diunggah dan diverifikasi! <<<")
            access_success = True
        else:
            print("\n!!! Verifikasi Data GAGAL: Data yang diakses TIDAK cocok atau tidak ditemukan. !!!")
            print("Data yang diharapkan (potongan):")
            print(f"  Patient ID (root): {patient_id_to_test}")
            print(f"  Patient ID (in data object): {patient_id_to_test}")
            print(f"  Status: CONFIRMED")
            print("Data yang diterima (potongan):")
            print(f"  Patient ID (root): {access_response_data.get('patientId')}")
            print(f"  Patient ID (in data object): {retrieved_main_data.get('patientID')}")
            print(f"  Status: {retrieved_main_data.get('status')}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Gagal mengakses data dari {access_url}.")
        print(f"Detail Error: {e}")
    except json.JSONDecodeError:
        print(f"ERROR: Respon akses dari {access_url} bukan JSON yang valid.")

    print("--- Pengujian End-to-End Unggah, Tunggu Verifikasi, Beri Izin, & Akses Selesai ---\n")

# --- Main Program ---
if __name__ == "__main__":
    print("Memulai program pengujian end-to-end (unggah, tunggu verifikasi internal, beri izin, akses data EKG)...")
    
    test_ecg_upload_grant_and_access()

    print("Program pengujian selesai.")