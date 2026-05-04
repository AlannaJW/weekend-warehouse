"""Load raw CSVs into BigQuery raw dataset."""

import os
from google.cloud import bigquery
from google.oauth2 import service_account

KEY_PATH = r"C:\Users\alann\Documents\Data Projects\gcp-keys\weekend-warehouse-f5a1723475b6.json"
PROJECT   = "weekend-warehouse"
DATASET   = "raw"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

TABLES = [
    "raw_customers",
    "raw_orders",
    "raw_tier_history",
    "raw_web_events",
]

credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
client = bigquery.Client(project=PROJECT, credentials=credentials)

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)

for table in TABLES:
    csv_path = os.path.join(DATA_DIR, f"{table}.csv")
    table_ref = f"{PROJECT}.{DATASET}.{table}"
    print(f"Loading {csv_path} -> {table_ref} ...", end=" ", flush=True)
    with open(csv_path, "rb") as f:
        job = client.load_table_from_file(f, table_ref, job_config=job_config)
    job.result()
    loaded = client.get_table(table_ref).num_rows
    print(f"{loaded:,} rows")

print("\nDone.")
