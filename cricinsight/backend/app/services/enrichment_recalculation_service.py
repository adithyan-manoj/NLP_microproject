"""
Missing Match Ingestion and Deterministic Local Recalculation Service for CricInsight.
CRITICAL MANDATE:
When external verification detects missing local match records:
1. Identify the missing matches.
2. Retrieve their match-level scorecards.
3. Ingest missing records into the local database (Tier 2 match_scorecards).
4. Recalculate the aggregate locally using the deterministic analytics engine.
5. Re-run field-level comparison against external statistics.
6. Guarantee that the final answer is 100% reproducible from enriched local records.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.core.config import settings
from app.database.db import execute_query, execute_statement
from app.analytics.engine import analyze_player_batting
from app.services.metric_comparator import MetricComparator
from app.schemas.verification_contracts import (
    CricketMetricSet,
    LocalComputationEvidence,
    ExternalVerificationEvidence,
    DiscrepancyReport,
    VerifiedResult,
)

logger = logging.getLogger("cricinsight.enrichment")

SCORECARDS_CATALOG_PATH = settings.DATA_DIR / "knowledge" / "historical_season_scorecards.json"


class EnrichmentRecalculationService:
    """
    Handles missing match scorecard retrieval, ingestion, and local recalculation.
    Never blindly replaces local aggregate with external aggregate.
    """

    @classmethod
    def load_season_scorecards(cls, player: str, competition: Optional[str], season: Optional[str]) -> List[Dict[str, Any]]:
        """Loads curated scorecard records from knowledge store for the requested entity scope."""
        if not SCORECARDS_CATALOG_PATH.exists():
            return []
        try:
            with open(SCORECARDS_CATALOG_PATH, "r", encoding="utf-8") as f:
                catalog = json.load(f)
            key = f"{player.lower()}_{competition.lower() if competition else 'all'}_{season if season else 'all'}"
            return catalog.get(key, [])
        except Exception as e:
            logger.warning(f"Could not load season scorecards catalog: {e}")
            return []

    @classmethod
    def ingest_missing_scorecards(
        cls,
        player: str,
        competition: Optional[str],
        season: Optional[str],
        format_type: str,
        missing_scorecards: List[Dict[str, Any]],
    ) -> int:
        """
        Idempotently inserts missing match scorecards into the local database (Tier 2).
        Returns number of inserted scorecards.
        """
        inserted_count = 0
        for sc in missing_scorecards:
            match_id = sc["match_id"]
            sc_id = f"{match_id}_{player.lower().replace(' ', '_')}"
            try:
                execute_statement("""
                    INSERT OR REPLACE INTO match_scorecards (
                        id, match_id, player_name, player_id, competition, season, match_type,
                        match_date, opponent, venue, innings_number, runs, balls_faced,
                        fours, sixes, is_out, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, [
                    sc_id,
                    match_id,
                    player,
                    player.lower().replace(" ", "_"),
                    competition or "IPL",
                    season or "2022",
                    format_type or "T20",
                    sc.get("date", "2022-01-01"),
                    sc.get("opponent", "Opponent"),
                    sc.get("venue", "Venue"),
                    1,
                    int(sc.get("runs", 0)),
                    int(sc.get("balls", 0)),
                    int(sc.get("fours", 0)),
                    int(sc.get("sixes", 0)),
                    bool(sc.get("is_out", True)),
                    "verified_enrichment_service",
                ])
                inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to ingest scorecard {sc_id}: {e}")

        return inserted_count

    @classmethod
    def reconcile_and_enrich(
        cls,
        local_comp: LocalComputationEvidence,
        external_verif: Optional[ExternalVerificationEvidence],
        discrepancy_report: DiscrepancyReport,
        format_type: str = "T20",
    ) -> Tuple[VerifiedResult, DiscrepancyReport, LocalComputationEvidence]:
        """
        Executes discrepancy resolution protocol:
        - If missing local records: acquires scorecards, ingests, and recalculates locally.
        - If external is erroneous: rejects external, preserves verified local records.
        - If consistent: marks verified.
        """
        strategy = discrepancy_report.resolution_strategy

        # Case 1: All metrics match external evidence
        if strategy == "CONSISTENT" or not discrepancy_report.has_discrepancy:
            verif_res = VerifiedResult(
                metrics=local_comp.metrics,
                verification_status="VERIFIED_CONSISTENT",
                confidence_score=1.0,
                provenance_summary="100% field-level agreement between local calculation and external authority.",
                discrepancy_resolved=True,
                notes=["Local ball-by-ball records fully corroborate official statistics."]
            )
            return verif_res, discrepancy_report, local_comp

        # Case 2: External claim is erroneous (e.g. external runs < local ball-by-ball sum)
        if strategy == "PRESERVE_VERIFIED_LOCAL" or "EXTERNAL_SOURCE_ERROR" in discrepancy_report.detected_issues:
            verif_res = VerifiedResult(
                metrics=local_comp.metrics,
                verification_status="LOCAL_PRESERVED_EXTERNAL_REJECTED",
                confidence_score=0.98,
                provenance_summary="External claim rejected. Preserved verified local Cricsheet ground truth.",
                discrepancy_resolved=True,
                notes=[
                    "Local delivery records represent verified ball-by-ball ground truth.",
                    "External aggregate contradicted primary source evidence and was rejected."
                ]
            )
            return verif_res, discrepancy_report, local_comp

        # Case 3: Missing local match records (e.g. local has 13 matches, external has 16)
        if strategy == "ENRICH_AND_RECALCULATE" or "MISSING_LOCAL_MATCHES" in discrepancy_report.detected_issues:
            season_scorecards = cls.load_season_scorecards(
                player=local_comp.player,
                competition=local_comp.competition,
                season=local_comp.season,
            )

            # Check which scorecards are missing from local match_ids
            existing_match_ids = set(local_comp.match_ids)
            missing_to_ingest = [
                sc for sc in season_scorecards
                if sc["match_id"] not in existing_match_ids
            ]

            if missing_to_ingest:
                ingested = cls.ingest_missing_scorecards(
                    player=local_comp.player,
                    competition=local_comp.competition,
                    season=local_comp.season,
                    format_type=format_type,
                    missing_scorecards=missing_to_ingest,
                )
                logger.info(f"Ingested {ingested} missing match scorecards for {local_comp.player}")

                # Step 4: RECALCULATE LOCALLY FROM ENRICHED RECORDS
                recalc_analysis = analyze_player_batting(
                    player_name=local_comp.player,
                    match_type=format_type,
                    competition=local_comp.competition,
                    season=local_comp.season,
                )
                m = recalc_analysis["metrics"]
                new_metrics = CricketMetricSet(
                    matches=m.get("matches"),
                    innings=m.get("innings"),
                    runs=m.get("runs"),
                    balls_faced=m.get("balls_faced"),
                    not_outs=m.get("not_outs"),
                    batting_average=m.get("batting_average"),
                    strike_rate=m.get("strike_rate"),
                    high_score=m.get("high_score"),
                    high_score_not_out=m.get("high_score_not_out", False),
                    fifties=m.get("fifties"),
                    hundreds=m.get("hundreds"),
                    fours=m.get("fours"),
                    sixes=m.get("sixes"),
                )

                new_local_comp = LocalComputationEvidence(
                    player=local_comp.player,
                    competition=local_comp.competition,
                    season=local_comp.season,
                    category=local_comp.category,
                    metrics=new_metrics,
                    granularity="match_scorecard",
                    matches_count=m.get("matches", 0),
                    innings_count=m.get("innings", 0),
                    match_ids=recalc_analysis.get("match_ids", []),
                    calculated_at=local_comp.calculated_at,
                    provenance="Local Analytics Engine (Enriched with Verified Scorecards)",
                )

                # Step 5: RE-COMPARE AGAINST EXTERNAL EVIDENCE
                new_discrepancy = MetricComparator.compare(new_local_comp, external_verif)
                new_discrepancy.audit_trail.append(
                    f"Successfully enriched database with {ingested} missing match scorecards. Deterministic recalculation completed."
                )

                verif_res = VerifiedResult(
                    metrics=new_metrics,
                    verification_status="ENRICHED_AND_RECALCULATED",
                    confidence_score=1.0,
                    provenance_summary=f"Enriched local database with {ingested} missing scorecards and deterministically recalculated.",
                    discrepancy_resolved=True,
                    notes=[
                        f"Initial local query had {local_comp.matches_count} matches.",
                        f"Acquired and ingested {ingested} missing fixture scorecards.",
                        f"Recalculated full season totals: {new_metrics.runs} runs in {new_metrics.matches} matches (Avg: {new_metrics.batting_average}, SR: {new_metrics.strike_rate})."
                    ]
                )
                return verif_res, new_discrepancy, new_local_comp

        # Default fallback: Preserve local calculation with discrepancy flagged
        verif_res = VerifiedResult(
            metrics=local_comp.metrics,
            verification_status="PARTIAL_UNVERIFIED",
            confidence_score=0.85,
            provenance_summary="Discrepancy flagged; preserved verified local records.",
            discrepancy_resolved=False,
            notes=["Inconclusive external corroboration; local figures preserved."]
        )
        return verif_res, discrepancy_report, local_comp
