# view_csv.py

import sys
import pandas as pd
from tabulate import tabulate

if len(sys.argv) != 2:
    print("❌ Gunakan: python view_csv.py path/to/file.csv")
    sys.exit(1)

csv_path = sys.argv[1]

try:
    df = pd.read_csv(csv_path)
    print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
except FileNotFoundError:
    print(f"❌ File tidak ditemukan: {csv_path}")
except Exception as e:
    print(f"❌ Gagal membaca file: {e}")
