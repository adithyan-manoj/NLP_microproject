#!/usr/bin/env python3
"""
CricInsight - Automated Cricsheet Dataset Downloader and Ingestion Utility.
Downloads official Cricsheet archives (IPL, ODIs, T20Is, people.csv registry),
extracts modern curated matches, and idempotently ingests them into the database.
"""

import sys
import os
import zipfile
import json
import tempfile
import argparse
import urllib.request
from pathlib import Path

# Set up paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.ingestion.ingestion_service import IngestionService
from app.services.dataset_service import get_dataset_coverage, get_dataset_status

CRICSHEET_URLS = {
    "ipl": "https://cricsheet.org/downloads/ipl_male_json.zip",
    "odis": "https://cricsheet.org/downloads/odis_male_json.zip",
    "t20s": "https://cricsheet.org/downloads/t20s_male_json.zip",
    "tests": "https://cricsheet.org/downloads/tests_male_json.zip",
    "people": "https://cricsheet.org/downloads/people.csv",
}

DEFAULT_TARGET_DIR = BACKEND_DIR / "data" / "cricsheet"
DEFAULT_PEOPLE_PATH = BACKEND_DIR / "data" / "people.csv"

def download_with_progress(url: str, dest_path: Path):
    """Downloads a file with clean console progress reporting."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading from: {url}")
    print(f"Destination:     {dest_path}")

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100.0, (downloaded / total_size) * 100.0)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  Progress: {percent:5.1f}% [{mb_downloaded:6.2f} MB / {mb_total:6.2f} MB]")
        else:
            mb_downloaded = downloaded / (1024 * 1024)
            sys.stdout.write(f"\r  Downloaded: {mb_downloaded:6.2f} MB")
        sys.stdout.flush()

    urllib.request.urlretrieve(url, str(dest_path), reporthook=reporthook)
    sys.stdout.write("\n")
    print(f"Downloaded successfully: {dest_path.name}")

def extract_curated_matches(zip_path: Path, output_dir: Path, max_matches: int = 150, min_date: str = "2021-01-01") -> int:
    """
    Extracts matches from the zip archive into the output directory.
    Filters for matches since min_date to prioritize modern star records.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    with zipfile.ZipFile(zip_path, 'r') as z:
        namelist = [n for n in z.namelist() if n.endswith('.json') and not n.startswith('__')]
        # Sort in reverse to get newest matches first
        namelist.sort(reverse=True)

        for name in namelist:
            if max_matches > 0 and count >= max_matches:
                break

            try:
                raw_bytes = z.read(name)
                match_data = json.loads(raw_bytes.decode('utf-8'))
                info = match_data.get('info', {})
                dates = info.get('dates', [])
                date_str = dates[0] if dates else ""

                if not min_date or date_str >= min_date or len(namelist) < max_matches:
                    target_file = output_dir / Path(name).name
                    target_file.write_bytes(raw_bytes)
                    count += 1
            except Exception:
                continue

    print(f"Extracted {count} curated matches into {output_dir}")
    return count

def main():
    parser = argparse.ArgumentParser(description="Download and ingest real Cricsheet data into CricInsight.")
    parser.add_argument("--pack", choices=["ipl", "odis", "t20s", "tests", "all"], default="ipl", help="Dataset archive pack to download")
    parser.add_argument("--limit", type=int, default=120, help="Maximum number of curated matches to extract and ingest per pack (default: 120)")
    parser.add_argument("--since", type=str, default="2020-01-01", help="Minimum match start date filter (default: 2020-01-01)")
    parser.add_argument("--target-dir", type=Path, default=DEFAULT_TARGET_DIR, help="Directory to store extracted JSON files")
    parser.add_argument("--skip-download", action="store_true", help="Skip download if zip already exists in temp")
    parser.add_argument("--no-ingest", action="store_true", help="Download only without triggering database ingestion")

    args = parser.parse_args()

    print("==================================================")
    print("  CRICINSIGHT — CRICSHEET DOWNLOADER & CURATOR")
    print("==================================================")

    temp_dir = Path(tempfile.gettempdir())
    packs_to_process = ["ipl", "odis", "t20s"] if args.pack == "all" else [args.pack]

    # Step 1: Download people.csv registry if needed
    if not DEFAULT_PEOPLE_PATH.exists():
        print("\n[Step 1/3] Downloading Cricsheet Player Registry (people.csv)...")
        try:
            download_with_progress(CRICSHEET_URLS["people"], DEFAULT_PEOPLE_PATH)
        except Exception as e:
            print(f"Warning: Could not fetch people.csv: {e}")
    else:
        print("\n[Step 1/3] Player registry already exists at data/people.csv")

    total_extracted = 0
    for p in packs_to_process:
        zip_dest = temp_dir / f"{p}_male_json.zip"
        print(f"\n[Step 2/3] Processing {p.upper()} match archive...")
        if not args.skip_download or not zip_dest.exists():
            download_with_progress(CRICSHEET_URLS[p], zip_dest)
        else:
            print(f"Using cached archive at: {zip_dest}")

        print(f"\n[Step 3/3] Extracting {p.upper()} matches (limit={args.limit}, min_date={args.since})...")
        total_extracted += extract_curated_matches(zip_dest, args.target_dir, max_matches=args.limit, min_date=args.since)

    # Step 4: Run Ingestion
    if not args.no_ingest and total_extracted > 0:

        print("\n==================================================")
        print("  INGESTING MATCHES INTO CRICINSIGHT DATABASE")
        print("==================================================")
        summary = IngestionService.import_directory(args.target_dir, force=False)
        print(f"\nIngestion Result:")
        print(f"  Processed: {summary.get('files_processed')} files")
        print(f"  Inserted:  {summary.get('inserted_count')} matches")
        print(f"  Updated:   {summary.get('updated_count')} matches")
        print(f"  Skipped:   {summary.get('skipped_count')} matches")
        print(f"  Errors:    {summary.get('rejected_count')}")

        cov = get_dataset_coverage()
        print(f"\nDatabase Coverage Now:")
        print(f"  Total Matches:    {cov.get('total_matches'):,}")
        print(f"  Total Formats:    {[f['match_type'] for f in cov.get('formats', [])]}")
        print(f"  Covered Teams:    {len(cov.get('teams', []))} teams")
        print("==================================================\n")

if __name__ == "__main__":
    main()
