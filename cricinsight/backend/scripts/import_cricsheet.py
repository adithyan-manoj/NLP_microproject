#!/usr/bin/env python3
"""
CLI Script to import Cricsheet JSON files into CricInsight database.
Ensures idempotency, records file hashes, updates existing matches safely,
and logs execution summary.
"""

import sys
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.ingestion_service import IngestionService
from app.services.dataset_service import get_dataset_coverage

def main():
    parser = argparse.ArgumentParser(description="Import Cricsheet match JSON files into CricInsight.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(Path(__file__).parent.parent / "data" / "fixtures"),
        help="Path to directory containing Cricsheet JSON files."
    )
    args = parser.parse_args()

    input_dir = Path(args.data_dir)
    if not input_dir.exists():
        print(f"Error: Directory '{input_dir}' does not exist.")
        sys.exit(1)

    print(f"==================================================")
    print(f"  CRICINSIGHT — CRICSHEET DATASET INGESTION")
    print(f"==================================================")
    print(f"Target Directory: {input_dir}")

    summary = IngestionService.import_directory(input_dir)

    print(f"\n--- Ingestion Summary ---")
    print(f"Status:          {summary.get('status')}")
    print(f"Files Processed: {summary.get('files_processed')}")
    print(f"Matches Added:   {summary.get('inserted_count')}")
    print(f"Matches Updated: {summary.get('updated_count')}")
    print(f"Matches Skipped: {summary.get('skipped_count')}")
    print(f"Failed Files:    {summary.get('rejected_count')}")

    coverage = get_dataset_coverage()
    print(f"\n--- Current Dataset Coverage ---")
    print(f"Total Matches:   {coverage.get('total_matches')}")
    print(f"Formats:         {[f['match_type'] for f in coverage.get('formats', [])]}")
    print(f"Covered Teams:   {len(coverage.get('teams', []))} teams")
    print(f"Last Ingestion:  {coverage.get('last_updated')}")
    print(f"==================================================\n")

if __name__ == "__main__":
    main()
