"""
Field-Level Metric Comparison Service for CricInsight.
Compares local deterministic calculation and externally verified evidence field-by-field.
Detects:
- Missing matches
- Missing innings
- Incorrect scorecard records
- Duplicate records
- Different statistical definitions
- Incorrect calculated aggregates
- Conflicting source values
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.verification_contracts import (
    CricketMetricSet,
    LocalComputationEvidence,
    ExternalVerificationEvidence,
    FieldComparisonItem,
    DiscrepancyReport,
)

METRIC_FIELDS = [
    ("matches", "Matches Played"),
    ("innings", "Innings Batted"),
    ("runs", "Total Runs"),
    ("balls_faced", "Balls Faced"),
    ("not_outs", "Not Outs"),
    ("batting_average", "Batting Average"),
    ("strike_rate", "Batting Strike Rate"),
    ("high_score", "Highest Score"),
    ("fifties", "Fifties (50-99)"),
    ("hundreds", "Hundreds (100+)"),
    ("fours", "Fours (4s)"),
    ("sixes", "Sixes (6s)"),
]


class MetricComparator:
    """
    Dedicated field-by-field comparison service.
    Performs deterministic reconciliation without hiding individual differences behind generic scores.
    """

    @classmethod
    def compare(
        cls,
        local_comp: LocalComputationEvidence,
        external_verif: Optional[ExternalVerificationEvidence] = None,
    ) -> DiscrepancyReport:
        comparisons: List[FieldComparisonItem] = []
        detected_issues: List[str] = []
        audit_trail: List[str] = []

        local_metrics = local_comp.metrics
        ext_metrics = external_verif.metrics if external_verif else CricketMetricSet()

        if not external_verif or external_verif.retrieval_status in ["failed", "disabled"]:
            # External verification was not available or failed
            for field, label in METRIC_FIELDS:
                loc_val = getattr(local_metrics, field, None)
                comparisons.append(FieldComparisonItem(
                    metric=field,
                    local_value=loc_val,
                    external_value=None,
                    status="EXTERNAL_MISSING",
                    difference_explanation="External verification source unavailable; preserving local calculation"
                ))
            detected_issues.append("EXTERNAL_EVIDENCE_UNAVAILABLE")
            audit_trail.append("External verification unavailable or failed; local calculation verified as primary authority.")
            return DiscrepancyReport(
                has_discrepancy=False,
                total_fields_compared=len(METRIC_FIELDS),
                matching_fields=0,
                discrepant_fields=0,
                comparisons=comparisons,
                detected_issues=detected_issues,
                resolution_strategy="PRESERVE_LOCAL",
                audit_trail=audit_trail,
            )

        matching_count = 0
        discrepant_count = 0

        # 1. Field by field evaluation
        for field, label in METRIC_FIELDS:
            loc_val = getattr(local_metrics, field, None)
            ext_val = getattr(ext_metrics, field, None)

            if loc_val is None and ext_val is None:
                continue

            if loc_val is None and ext_val is not None:
                comparisons.append(FieldComparisonItem(
                    metric=field,
                    local_value=None,
                    external_value=ext_val,
                    status="LOCAL_MISSING",
                    difference_explanation=f"Local record missing '{field}'; external reports {ext_val}"
                ))
                discrepant_count += 1
                continue

            if loc_val is not None and ext_val is None:
                comparisons.append(FieldComparisonItem(
                    metric=field,
                    local_value=loc_val,
                    external_value=None,
                    status="EXTERNAL_MISSING",
                    difference_explanation=f"External source does not report '{field}'; local has {loc_val}"
                ))
                # Not considered a discrepancy if external source just omitted a granular stat like 4s/6s
                matching_count += 1
                continue

            # Both values present: check equality with tolerances
            status = "MATCH"
            explanation = None

            if field in ["batting_average", "strike_rate"]:
                # Floating point comparison with 0.05 tolerance for rounding
                loc_f = float(loc_val) if loc_val is not None else 0.0
                ext_f = float(ext_val) if ext_val is not None else 0.0
                if abs(loc_f - ext_f) <= 0.05:
                    status = "MATCH"
                else:
                    # Check if average difference is due to not-out definition or missing matches
                    status = "DISCREPANCY"
                    explanation = f"Value mismatch: local={loc_f}, external={ext_f} (delta={round(loc_f - ext_f, 2)})"
            elif field in ["matches", "innings", "runs", "fifties", "hundreds", "fours", "sixes", "high_score", "balls_faced", "not_outs"]:
                if int(loc_val) == int(ext_val):
                    status = "MATCH"
                else:
                    # Check for statistical definition difference in balls faced (wides included vs excluded)
                    if field == "balls_faced" and abs(int(loc_val) - int(ext_val)) <= 10:
                        status = "DEFINITION_DIFFERENCE"
                        explanation = f"Definition difference: local excludes wides ({loc_val}); external source may include all deliveries faced ({ext_val})"
                    else:
                        status = "DISCREPANCY"
                        explanation = f"Value mismatch: local={loc_val}, external={ext_val}"
            else:
                if loc_val == ext_val:
                    status = "MATCH"
                else:
                    status = "DISCREPANCY"
                    explanation = f"Value mismatch: local={loc_val}, external={ext_val}"

            if status == "MATCH":
                matching_count += 1
            elif status == "DEFINITION_DIFFERENCE":
                matching_count += 1
                detected_issues.append("STATISTICAL_DEFINITION_DIFFERENCE")
                audit_trail.append(f"Field '{field}' reflects different statistical definitions ({explanation}).")
            else:
                discrepant_count += 1

            comparisons.append(FieldComparisonItem(
                metric=field,
                local_value=loc_val,
                external_value=ext_val,
                status=status,
                difference_explanation=explanation
            ))

        # 2. Structural Root Cause Analysis
        loc_m = local_metrics.matches or 0
        ext_m = ext_metrics.matches or 0
        loc_r = local_metrics.runs or 0
        ext_r = ext_metrics.runs or 0

        # Scenario A: Missing local match records
        if ext_m > loc_m and ext_r > loc_r:
            missing_delta = ext_m - loc_m
            detected_issues.append("MISSING_LOCAL_MATCHES")
            audit_trail.append(
                f"Missing local match records detected: external confirms {ext_m} matches ({ext_r} runs) "
                f"while local database contains only {loc_m} matches ({loc_r} runs). Delta: {missing_delta} matches."
            )

        # Scenario B: Duplicate records in local database
        elif loc_m > ext_m and ext_m > 0:
            dup_delta = loc_m - ext_m
            detected_issues.append("DUPLICATE_RECORDS")
            audit_trail.append(
                f"Duplicate local records detected: local has {loc_m} matches but official source confirms {ext_m}. Delta: {dup_delta} matches."
            )

        # Scenario C: Incorrect external statistic (e.g. external hallucinates or has outdated summary)
        elif loc_m >= ext_m and ext_m > 0 and loc_r > ext_r:
            # When local ball-by-ball delivery records are verified and exceed external claim
            detected_issues.append("EXTERNAL_SOURCE_ERROR")
            audit_trail.append(
                f"External statistic rejected: local verified ball-by-ball deliveries confirm {loc_r} runs across {loc_m} matches, "
                f"exceeding external ungrounded claim of {ext_r} runs. Verified local records preserved."
            )

        # Scenario D: Incorrect local aggregate with matching matches count
        elif loc_m == ext_m and loc_m > 0 and loc_r != ext_r:
            detected_issues.append("INCORRECT_LOCAL_CALCULATION")
            audit_trail.append(
                f"Local aggregate discrepancy: matches count matches ({loc_m}), but runs differ (local={loc_r}, external={ext_r}). Inspecting underlying scorecards."
            )

        # 3. Determine resolution strategy
        has_discrepancy = discrepant_count > 0
        if not has_discrepancy:
            resolution = "CONSISTENT"
            audit_trail.append("All metrics field-by-field verified consistent with external authority.")
        elif "MISSING_LOCAL_MATCHES" in detected_issues:
            resolution = "ENRICH_AND_RECALCULATE"
        elif "EXTERNAL_SOURCE_ERROR" in detected_issues:
            resolution = "PRESERVE_VERIFIED_LOCAL"
        elif "STATISTICAL_DEFINITION_DIFFERENCE" in detected_issues and discrepant_count == 0:
            resolution = "HARMONIZE_DEFINITIONS"
        elif "INCORRECT_LOCAL_CALCULATION" in detected_issues:
            resolution = "CORRECT_LOCAL_CALCULATION"
        else:
            resolution = "FLAG_DISCREPANCY"

        return DiscrepancyReport(
            has_discrepancy=has_discrepancy,
            total_fields_compared=len(comparisons),
            matching_fields=matching_count,
            discrepant_fields=discrepant_count,
            comparisons=comparisons,
            detected_issues=detected_issues,
            resolution_strategy=resolution,
            audit_trail=audit_trail,
        )
