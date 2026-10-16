"""CareFlow: Google BigQuery Data Ingestion Script.

Loads raw healthcare event log data (CSV) into Google BigQuery.

Security & Reproducibility Guidelines:
--------------------------------------
1. No hardcoded credentials or project IDs.
2. Reads configuration from environment variables or command-line arguments:
   - GCP Project ID: --project-id or env var BIGQUERY_PROJECT_ID
   - Dataset ID: --dataset-id or env var BIGQUERY_DATASET_ID (default: careflow_raw)
   - Credentials: GOOGLE_APPLICATION_CREDENTIALS env var (path to service account JSON)
     OR active gcloud application-default credentials.

Prerequisites:
--------------
- Python package: google-cloud-bigquery (pip install google-cloud-bigquery db-dtypes)
- Google Cloud Project with BigQuery API enabled.
"""

import argparse
import os
from pathlib import Path
import sys

# File Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log_v2.csv"
FALLBACK_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"


def check_prerequisites():
    """Verify if google-cloud-bigquery is installed."""
    try:
        from google.cloud import bigquery  # noqa: F401
        return True, "google-cloud-bigquery is installed"
    except ImportError:
        return False, "Missing python package: google-cloud-bigquery (run: pip install google-cloud-bigquery db-dtypes)"


def upload_csv_to_bigquery(
    project_id: str,
    dataset_id: str,
    table_id: str,
    csv_path: Path,
) -> bool:
    """Upload CSV to Google BigQuery and verify row count."""
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound

    if not csv_path.exists():
        print(f"Error: CSV file not found at: {csv_path}")
        return False

    print(f"Initializing BigQuery client for Project: '{project_id}'...")
    client = bigquery.Client(project=project_id)

    # 1. Ensure Dataset Exists
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"  [OK] Dataset '{dataset_id}' exists.")
    except NotFound:
        print(f"  Creating dataset '{dataset_id}' in project '{project_id}'...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"  # Default location
        client.create_dataset(dataset, timeout=30)
        print(f"  [OK] Dataset '{dataset_id}' created successfully.")

    # 2. Configure Load Job
    table_ref = dataset_ref.table(table_id)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replaces on rerun
    )

    print(f"Uploading '{csv_path.name}' to table '{dataset_id}.{table_id}'...")
    with open(csv_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_ref, job_config=job_config)

    job.result()  # Wait for the load job to complete
    print(f"  [OK] BigQuery load job completed successfully.")

    # 3. Verify Table and Row Count
    destination_table = client.get_table(table_ref)
    print(f"\n--- BigQuery Upload Verification ---")
    print(f"  Table Name    : {destination_table.full_table_id}")
    print(f"  Rows Ingested : {destination_table.num_rows:,}")
    print(f"  Table Size    : {destination_table.num_bytes / 1024:.2f} KB")

    # Run quick sanity query
    query = f"SELECT COUNT(*) AS total_rows FROM `{project_id}.{dataset_id}.{table_id}`;"
    query_job = client.query(query)
    results = list(query_job.result())
    verified_rows = results[0]["total_rows"]
    print(f"  Verified Count: {verified_rows:,} rows via SQL query.")

    return True


def main():
    parser = argparse.ArgumentParser(description="Upload CareFlow raw event logs to Google BigQuery.")
    parser.add_argument("--project-id", default=os.getenv("BIGQUERY_PROJECT_ID"), help="GCP Project ID")
    parser.add_argument("--dataset-id", default=os.getenv("BIGQUERY_DATASET_ID", "careflow_raw"), help="BigQuery Dataset ID")
    parser.add_argument("--table-id", default="raw_healthcare_events", help="BigQuery Table ID")
    parser.add_argument("--csv-path", default=str(DEFAULT_CSV if DEFAULT_CSV.exists() else FALLBACK_CSV), help="Path to raw CSV")

    args = parser.parse_args()

    # Step 1: Check Python dependencies
    installed, msg = check_prerequisites()
    if not installed:
        print("\n====================================================================")
        print("          Google BigQuery Upload: Prerequisites Check               ")
        print("====================================================================")
        print(f" [STATUS] BLOCKED: {msg}")
        print("\nTo enable BigQuery integration, install the required packages:")
        print("  pip install google-cloud-bigquery db-dtypes")
        print("====================================================================\n")
        sys.exit(0)

    # Step 2: Check GCP Project Configuration
    if not args.project_id:
        print("\n====================================================================")
        print("          Google BigQuery Upload: Configuration Needed              ")
        print("====================================================================")
        print(" [STATUS] BLOCKED: GCP Project ID is not specified.")
        print("\nPlease provide your GCP Project ID:")
        print("  Option A (CLI): python src/upload_to_bigquery.py --project-id YOUR_PROJECT_ID")
        print("  Option B (Env): $env:BIGQUERY_PROJECT_ID='YOUR_PROJECT_ID'")
        print("\nAlso ensure authentication is configured:")
        print("  1. Run: gcloud auth application-default login")
        print("     OR set $env:GOOGLE_APPLICATION_CREDENTIALS='path/to/keyfile.json'")
        print("====================================================================\n")
        sys.exit(0)

    try:
        success = upload_csv_to_bigquery(
            project_id=args.project_id,
            dataset_id=args.dataset_id,
            table_id=args.table_id,
            csv_path=Path(args.csv_path),
        )
        if not success:
            sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] BigQuery upload failed: {exc}")
        print("Check that your project ID is valid, BigQuery API is enabled, and your account has 'BigQuery Data Editor' permissions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
