"""
Comprehensive Acceptance Tests for Independent Analytics and Parallel External Verification.
Demonstrates the 10 core architectural scenarios required by CricInsight:
1. Complete local statistics with matching external evidence.
2. Missing local match records detected by external verification.
3. Incorrect local aggregate detected and corrected.
4. Incorrect external statistic rejected (protecting verified local ground truth).
5. Duplicate matches detected.
6. Different statistical definitions handled correctly (e.g. wides in strike rate).
7. Partial scorecard coverage handled without requiring ball-by-ball data.
8. Enrichment followed by independent local recalculation.
9. Subsequent identical queries retrieving enriched local records.
10. External retrieval failure without fabricated results.
"""

import pytest
import pandas as pd
from typing import Dict, Any

from app.schemas.verification_contracts import (
    CricketMetricSet,
    LocalComputationEvidence,
    ExternalVerificationEvidence,
    DiscrepancyReport,
    VerifiedResult,
)
from app.services.metric_comparator import MetricComparator
from app.services.enrichment_recalculation_service import EnrichmentRecalculationService
from app.analytics.cricket_metrics import calculate_batting_metrics
from app.database.db import execute_statement, execute_query


def test_scenario_1_complete_local_statistics_with_matching_external_evidence():
    """
    Scenario 1: Complete local statistics match external evidence 100% field-by-field.
    """
    local_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        matches_count=16,
        innings_count=16,
    )
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="IPL Official Archive / ESPNcricinfo",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)

    assert report.has_discrepancy is False
    assert report.matching_fields == 12
    assert report.discrepant_fields == 0
    assert report.resolution_strategy == "CONSISTENT"


def test_scenario_2_missing_local_match_records_detected():
    """
    Scenario 2: Missing local match records detected (e.g. local has 13 matches, external confirms 16).
    """
    local_metrics = CricketMetricSet(
        matches=13,
        innings=13,
        runs=236,
        balls_faced=208,
        not_outs=1,
        batting_average=19.67,
        strike_rate=113.46,
        high_score=58,
        fifties=1,
        hundreds=0,
        fours=21,
        sixes=6,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        matches_count=13,
        innings_count=13,
        match_ids=[f"ipl_2022_{i:02d}" for i in range(1, 14)],
    )
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="IPL Official Archive / ESPNcricinfo",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)

    assert report.has_discrepancy is True
    assert "MISSING_LOCAL_MATCHES" in report.detected_issues
    assert report.resolution_strategy == "ENRICH_AND_RECALCULATE"
    # Individual field comparisons check
    matches_comp = next(c for c in report.comparisons if c.metric == "matches")
    assert matches_comp.status == "DISCREPANCY"
    assert matches_comp.local_value == 13
    assert matches_comp.external_value == 16


def test_scenario_3_incorrect_local_aggregate_detected_and_corrected():
    """
    Scenario 3: Local calculation bug or aggregate mismatch detected and flagged for correction.
    """
    # Matches count matches (16), but total runs is mathematically wrong locally
    local_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=320,  # Corrupted aggregate
        balls_faced=294,
        not_outs=1,
        batting_average=21.33,
        strike_rate=108.84,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        matches_count=16,
        innings_count=16,
    )
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="IPL Official Archive",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)

    assert report.has_discrepancy is True
    assert "INCORRECT_LOCAL_CALCULATION" in report.detected_issues
    assert report.resolution_strategy == "CORRECT_LOCAL_CALCULATION"


def test_scenario_4_incorrect_external_statistic_rejected():
    """
    Scenario 4: Incorrect external statistic rejected, protecting verified local ground truth.
    Local verified ball-by-ball deliveries show 341 runs; external source erroneously claims 250 runs.
    """
    local_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        granularity="ball_by_ball",
        matches_count=16,
        innings_count=16,
    )
    # Erroneous external claim
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=250,  # Contradicts primary delivery ground truth
        balls_faced=294,
        not_outs=1,
        batting_average=16.66,
        strike_rate=85.03,
        high_score=50,
        fifties=1,
        hundreds=0,
        fours=20,
        sixes=5,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="Ungrounded Third Party Source",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)
    assert "EXTERNAL_SOURCE_ERROR" in report.detected_issues
    assert report.resolution_strategy == "PRESERVE_VERIFIED_LOCAL"

    verif_res, _, _ = EnrichmentRecalculationService.reconcile_and_enrich(
        local_comp=local_comp,
        external_verif=ext_verif,
        discrepancy_report=report,
    )
    assert verif_res.verification_status == "LOCAL_PRESERVED_EXTERNAL_REJECTED"
    assert verif_res.metrics.runs == 341


def test_scenario_5_duplicate_matches_detected():
    """
    Scenario 5: Duplicate matches in local database detected.
    """
    local_metrics = CricketMetricSet(
        matches=18,  # Duplicate fixtures ingested
        innings=18,
        runs=390,
        balls_faced=330,
        not_outs=1,
        batting_average=22.94,
        strike_rate=118.18,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=36,
        sixes=9,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        matches_count=18,
        innings_count=18,
    )
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="IPL Official Archive",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)
    assert "DUPLICATE_RECORDS" in report.detected_issues


def test_scenario_6_different_statistical_definitions_handled():
    """
    Scenario 6: Different statistical definitions handled correctly (e.g. balls faced / strike rate with or without wides).
    """
    # Local excludes wides (294 balls), external includes all deliveries (298 balls)
    local_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        matches_count=16,
        innings_count=16,
    )
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=298,  # Wides counted in total deliveries faced
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="Alternative Cricket Portal",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)
    bf_comp = next(c for c in report.comparisons if c.metric == "balls_faced")
    assert bf_comp.status == "DEFINITION_DIFFERENCE"
    assert "STATISTICAL_DEFINITION_DIFFERENCE" in report.detected_issues


def test_scenario_7_partial_scorecard_coverage_without_ball_by_ball():
    """
    Scenario 7: Partial scorecard coverage handled without requiring ball-by-ball delivery data.
    """
    scorecard_df = pd.DataFrame([
        {"match_id": "sc_01", "runs": 65, "balls_faced": 50, "fours": 6, "sixes": 2, "is_out": 1},
        {"match_id": "sc_02", "runs": 45, "balls_faced": 35, "fours": 4, "sixes": 1, "is_out": 0},
    ])
    metrics = calculate_batting_metrics(scorecard_df, "Kapil Dev", matches_count=2)

    assert metrics["matches"] == 2
    assert metrics["innings"] == 2
    assert metrics["runs"] == 110
    assert metrics["batting_average"] == 110.0  # 110 runs / 1 dismissal
    assert metrics["strike_rate"] == round((110 / 85) * 100, 2)
    assert metrics["fifties"] == 1
    assert metrics["high_score"] == 65


def test_scenario_8_enrichment_followed_by_independent_local_recalculation():
    """
    Scenario 8: Missing match scorecards are ingested and deterministically recalculated locally.
    Initial local data has 13 matches (236 runs); external confirms 16 matches (341 runs).
    The service ingests the 3 missing scorecards and recalculates locally to exactly 341 runs.
    """
    # Clean scorecards table for test isolation
    execute_statement("DELETE FROM match_scorecards WHERE player_name = 'Virat Kohli';")

    # Seed initial partial database state (first 13 matches only)
    all_scorecards = EnrichmentRecalculationService.load_season_scorecards("Virat Kohli", "IPL", "2022")
    initial_13 = all_scorecards[:13]
    EnrichmentRecalculationService.ingest_missing_scorecards("Virat Kohli", "IPL", "2022", "T20", initial_13)

    from app.analytics.engine import analyze_player_batting
    initial_analysis = analyze_player_batting(
        player_name="Virat Kohli",
        competition="IPL",
        season="2022",
        match_type="T20"
    )
    init_m = initial_analysis["metrics"]
    assert init_m["matches"] == 13
    assert init_m["runs"] == 236

    local_metrics = CricketMetricSet(
        matches=13,
        innings=13,
        runs=236,
        balls_faced=208,
        not_outs=1,
        batting_average=19.67,
        strike_rate=113.46,
        high_score=58,
        fifties=1,
        hundreds=0,
        fours=21,
        sixes=6,
    )
    local_comp = LocalComputationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=local_metrics,
        matches_count=13,
        innings_count=13,
        match_ids=[f"ipl_2022_{i:02d}" for i in range(1, 14)],
    )
    ext_metrics = CricketMetricSet(
        matches=16,
        innings=16,
        runs=341,
        balls_faced=294,
        not_outs=1,
        batting_average=22.73,
        strike_rate=115.98,
        high_score=73,
        fifties=2,
        hundreds=0,
        fours=32,
        sixes=8,
    )
    ext_verif = ExternalVerificationEvidence(
        player="Virat Kohli",
        competition="IPL",
        season="2022",
        metrics=ext_metrics,
        source_name="IPL Official Archive",
        retrieval_status="success",
    )

    report = MetricComparator.compare(local_comp, ext_verif)
    assert report.resolution_strategy == "ENRICH_AND_RECALCULATE"

    verif_res, new_report, new_local = EnrichmentRecalculationService.reconcile_and_enrich(
        local_comp=local_comp,
        external_verif=ext_verif,
        discrepancy_report=report,
        format_type="T20"
    )

    assert verif_res.verification_status == "ENRICHED_AND_RECALCULATED"
    assert verif_res.metrics.matches == 16
    assert verif_res.metrics.runs == 341
    assert verif_res.metrics.batting_average == 22.73
    assert abs(verif_res.metrics.strike_rate - 115.98) <= 0.05
    assert verif_res.metrics.high_score == 73
    assert verif_res.metrics.fifties == 2
    assert verif_res.metrics.fours == 32
    assert verif_res.metrics.sixes == 8


def test_scenario_9_subsequent_identical_queries_retrieving_enriched_local_records():
    """
    Scenario 9: Once enriched, subsequent identical queries retrieve enriched local records immediately.
    """
    from app.analytics.engine import analyze_player_batting
    analysis = analyze_player_batting(
        player_name="Virat Kohli",
        competition="IPL",
        season="2022",
        match_type="T20"
    )
    m = analysis["metrics"]
    assert m["matches"] == 16
    assert m["runs"] == 341
    assert m["batting_average"] == 22.73
    assert abs(m["strike_rate"] - 115.98) <= 0.05
    assert m["high_score"] == 73
    assert m["fours"] == 32
    assert m["sixes"] == 8


def test_scenario_10_external_retrieval_failure_without_fabricated_results():
    """
    Scenario 10: External retrieval failure handled gracefully without fabricating statistical values.
    """
    local_metrics = CricketMetricSet(
        matches=5,
        innings=5,
        runs=176,
        balls_faced=137,
        not_outs=1,
        batting_average=44.0,
        strike_rate=128.47,
        high_score=80,
        fifties=1,
        hundreds=0,
        fours=18,
        sixes=5,
    )
    local_comp = LocalComputationEvidence(
        player="Rohit Sharma",
        competition="T20",
        season="2024",
        metrics=local_metrics,
        matches_count=5,
        innings_count=5,
    )
    # External verification failed (e.g. offline / rate limit)
    ext_verif = ExternalVerificationEvidence(
        player="Rohit Sharma",
        competition="T20",
        season="2024",
        metrics=CricketMetricSet(),
        source_name="External Source",
        retrieval_status="failed",
        error_message="Network timeout connecting to external cricket archives"
    )

    report = MetricComparator.compare(local_comp, ext_verif)
    assert report.has_discrepancy is False
    assert report.resolution_strategy == "PRESERVE_LOCAL"
    assert "EXTERNAL_EVIDENCE_UNAVAILABLE" in report.detected_issues

    verif_res, _, _ = EnrichmentRecalculationService.reconcile_and_enrich(
        local_comp=local_comp,
        external_verif=ext_verif,
        discrepancy_report=report,
    )
    assert verif_res.metrics.runs == 176  # Preserves verified local calculation
    assert verif_res.metrics.batting_average == 44.0
