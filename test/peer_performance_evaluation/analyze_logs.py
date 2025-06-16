import os
import re
import pandas as pd
from glob import glob

# === Cari folder pengujian terbaru ===
base_path = "./"
pengujian_dirs = sorted(
    [d for d in glob(os.path.join(base_path, "pengujian_*")) if os.path.isdir(d)],
    key=os.path.getmtime,
    reverse=True
)

if not pengujian_dirs:
    print("❌ Tidak ditemukan folder pengujian_*")
else:
    pengujian_dir = pengujian_dirs[0]
    logs_dir = os.path.join(pengujian_dir, "logs")
    output_dir = os.path.join(pengujian_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # === Regex baru sesuai output fetch_peer_logs.sh
    pattern = re.compile(
        r"Block=(\d+)\s*\|\s*Time=(\d+)ms\s*\(state_validation=(\d+)ms block_and_pvtdata_commit=(\d+)ms state_commit=(\d+)ms\)\s*\|\s*Hash=([a-f0-9]*)"
    )

    log_data = []
    for filepath in glob(os.path.join(logs_dir, "*.log")):
        peer_name = os.path.basename(filepath).replace(".log", "")
        with open(filepath, 'r') as file:
            for line in file:
                match = pattern.search(line)
                if match:
                    log_data.append({
                        "Peer": peer_name,
                        "Block": int(match.group(1)),
                        "TransactionTime(ms)": int(match.group(2)),
                        "StateValidation(ms)": int(match.group(3)),
                        "BlockAndPvtDataCommit(ms)": int(match.group(4)),
                        "StateCommit(ms)": int(match.group(5)),
                        "CommitHash": match.group(6)
                    })

    df = pd.DataFrame(log_data)
    df = pd.DataFrame(log_data)
    if df.empty:
        print("❌ Tidak ada data berhasil diparse dari logs.")
    else:
        df_grouped = df.groupby(["Block", "Peer"], as_index=False).mean(numeric_only=True)

        # === Tabel 1: TransactionTime
        pivot_time = df_grouped.pivot(index="Block", columns="Peer", values="TransactionTime(ms)").sort_index()
        pivot_time.to_csv(os.path.join(output_dir, "tabel1_transaction_time.csv"))

        # === Tabel 2a: StateValidation
        pivot_sv = df_grouped.pivot(index="Block", columns="Peer", values="StateValidation(ms)").sort_index()
        pivot_sv.to_csv(os.path.join(output_dir, "tabel2a_state_validation_time.csv"))

        # === Tabel 2b: BlockAndPvtDataCommit
        pivot_bpdc = df_grouped.pivot(index="Block", columns="Peer", values="BlockAndPvtDataCommit(ms)").sort_index()
        pivot_bpdc.to_csv(os.path.join(output_dir, "tabel2b_block_and_pvtdata_commit_time.csv"))

        # === Tabel 2c: StateCommit
        pivot_sc = df_grouped.pivot(index="Block", columns="Peer", values="StateCommit(ms)").sort_index()
        pivot_sc.to_csv(os.path.join(output_dir, "tabel2c_state_commit_time.csv"))

        # === Tabel 3: Summary
        summary_df = df.groupby("Peer")["TransactionTime(ms)"].agg(
            AvgTime_ms="mean",
            MinTime_ms="min",
            MaxTime_ms="max"
        ).reset_index()
        summary_df.to_csv(os.path.join(output_dir, "tabel3_summary_transaction_time.csv"), index=False)

        print(f"✅ Semua tabel telah diekspor ke: {output_dir}")
