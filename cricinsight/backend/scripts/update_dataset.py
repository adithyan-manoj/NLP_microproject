#!/usr/bin/env python3
"""
CLI Script to perform incremental updates of the Cricsheet dataset in CricInsight.
Scans for new or modified JSON match files, validates file hashes, updates existing
matches safely, and displays updated coverage metrics.
"""

import sys
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.ingestion_service import IngestionService
from app.services.dataset_service import get_dataset_coverage, get_dataset_status

def main():
    parser = argparse.ArgumentParser(description="Incrementally update Cricsheet match files into CricInsight.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(Path(__file__).parent.parent / "data" / "fixtures"),
        help="Path to directory containing Cricsheet JSON files to update."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-import and update of all match files regardless of hash."
    )
    args = parser.parse_args()

    input_dir = Path(args.data_dir)
    if not input_dir.exists():
        print(f"Error: Target directory '{input_dir}' does not exist.")
        sys.exit(1)

    print("==================================================")
    print("  CRICINSIGHT — DATASET INCREMENTAL UPDATER")
    print("==================================================")
    print(f"Directory: {input_dir}")
    print(f"Force Mode: {'Enabled' if args.force else 'Disabled (Skip unchanged hashes)'}")

    # Check pre-update status
    pre_status = get_dataset_status()
    print(f"\nPre-update matches in DB: {pre_status.get('matches_count', 0)}")

    summary = IngestionService.import_directory(input_dir, force=args.force)

    print(f"\n--- Update Results ---")
    print(f"Status:          {summary.get('status')}")
    print(f"Files Inspected: {summary.get('files_processed')}")
    print(f"New Matches:     {summary.get('inserted_count')}")
    print(f"Updated Matches: {summary.get('updated_count')}")
    print(f"Unchanged Files: {summary.get('skipped_count')}")
    print(f"Rejected Files:  {summary.get('rejected_count')}")

    # Post-update coverage
    post_coverage = get_dataset_coverage()
    print(f"\n--- Fresh Dataset Coverage ---")
    print(f"Total Matches:   {post_coverage.get('total_matches')}")
    print(f"Formats:         {[f['match_type'] for f in post_coverage.get('formats', [])]}")
    print(f"Competitions:    {len(post_coverage.get('competitions', []))}")
    print(f"Teams:           {len(post_coverage.get('teams', []))}")
    print(f"Last Refreshed:  {post_coverage.get('last_updated')}")
    print("==================================================\n")

if __name__ == "__main__":
    main()
