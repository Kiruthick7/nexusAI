"""
Module implementing the Pattern Evaluation Engine.
Orchestrates loading historical claims, executing modular behavioral detectors,
streaming progressive telemetry checkpoints, and compiling aggregated findings with Gemma.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List

from app.models.enums import AgentName, Severity, AgentStatus
from app.models.evidence import Evidence
from app.models.mission_context import SharedMissionContext
from app.policy.loader import load_policies
from app.core.logger import logger
from app.core.event_publisher import (
    publish_pattern_history_loaded,
    publish_pattern_check_started,
    publish_pattern_finding,
    publish_pattern_summary_generated,
)
from app.pattern.models import PatternFinding
from app.pattern.loader import load_historical_claims
from app.pattern.detectors import (
    check_duplicate_invoice,
    check_claim_frequency,
    check_vendor_anomaly,
    check_weekend_submission,
    check_split_billing,
    check_near_limit,
)
from app.pattern.summarizer import generate_behavioral_summary


class PatternEvaluator:
    """
    Core engine managing execution pipelines and checkpoint communications for Pattern Agent.
    """
    def __init__(self):
        # Cache policies configuration loader
        self._policies = None

    def _get_category_limit(self, category: str) -> float:
        """
        Retrieves the maximum allowed limit for a corporate spend category.
        """
        if not self._policies:
            try:
                self._policies = load_policies()
            except Exception as err:
                logger.error(f"[PATTERN ENGINE] Failed to load policies from policy module: {str(err)}")
                return 5000.0  # Safe standard fallback limit

        # Fallback to standard limit if category is missing
        if not category or category not in self._policies:
            return 5000.0

        return self._policies[category].max_amount

    async def evaluate_patterns(
        self,
        mission_id: str,
        context: SharedMissionContext,
        simulate_db_timeout: bool = False
    ) -> Evidence:
        """
        Runs the pattern auditing pipeline.
        
        Fetches historical records, executes checks, publishes progressive SSE events,
        synthesizes findings via Gemma, and compiles a canonical Evidence result.
        """
        logger.info(f"[PATTERN ENGINE] Beginning pattern analysis sequence for mission_id={mission_id}")

        employee_id = context.employee_id
        current_claim_id = context.claim_id
        current_amount = context.amount or 0.0
        current_invoice = context.invoice_number or ""
        current_vendor = context.vendor_name or ""
        current_category = context.category or ""
        current_date = context.date or ""

        # 1. Fetch Historical Claims (Loader)
        history = await load_historical_claims(
            employee_id=employee_id,
            current_claim_id=current_claim_id,
            simulate_timeout=simulate_db_timeout
        )
        
        # Stream historical records loaded checkpoint event
        await publish_pattern_history_loaded(mission_id=mission_id, count=len(history))

        # 2. Run Modular Evaluators & Emit granular SSE checkpoints
        findings: List[PatternFinding] = []
        max_allowed_limit = self._get_category_limit(current_category)

        # -- Check A: Duplicate Invoice Check --
        await publish_pattern_check_started(mission_id, "Duplicate Invoice Scanner")
        dup_finding = check_duplicate_invoice(current_invoice, current_amount, history)
        findings.append(dup_finding)
        await publish_pattern_finding(
            mission_id=mission_id,
            pattern_type=dup_finding.pattern_type,
            result=dup_finding.result,
            details=dup_finding.evidence,
            severity=dup_finding.severity,
            metadata={"supporting_claims_count": len(dup_finding.supporting_claims)}
        )

        # -- Check B: Claim Frequency Check --
        await publish_pattern_check_started(mission_id, "Anomalous Claim Frequency Evaluator")
        freq_finding = check_claim_frequency(current_date, history)
        findings.append(freq_finding)
        await publish_pattern_finding(
            mission_id=mission_id,
            pattern_type=freq_finding.pattern_type,
            result=freq_finding.result,
            details=freq_finding.evidence,
            severity=freq_finding.severity,
            metadata={"supporting_claims_count": len(freq_finding.supporting_claims)}
        )

        # -- Check C: Same-Day Vendor Repetition Check --
        await publish_pattern_check_started(mission_id, "Same-Day Vendor Repetition Matcher")
        vendor_finding = check_vendor_anomaly(current_date, current_vendor, history)
        findings.append(vendor_finding)
        await publish_pattern_finding(
            mission_id=mission_id,
            pattern_type=vendor_finding.pattern_type,
            result=vendor_finding.result,
            details=vendor_finding.evidence,
            severity=vendor_finding.severity,
            metadata={"supporting_claims_count": len(vendor_finding.supporting_claims)}
        )

        # -- Check D: Weekend Submission Check --
        await publish_pattern_check_started(mission_id, "Weekend Activity Evaluator")
        weekend_finding = check_weekend_submission(current_date)
        findings.append(weekend_finding)
        await publish_pattern_finding(
            mission_id=mission_id,
            pattern_type=weekend_finding.pattern_type,
            result=weekend_finding.result,
            details=weekend_finding.evidence,
            severity=weekend_finding.severity
        )

        # -- Check E: Split Billing Check --
        await publish_pattern_check_started(mission_id, "Split-Billing Limit evasion Scanner")
        split_finding = check_split_billing(
            current_date,
            current_vendor,
            current_amount,
            current_category,
            history,
            max_allowed_limit
        )
        findings.append(split_finding)
        await publish_pattern_finding(
            mission_id=mission_id,
            pattern_type=split_finding.pattern_type,
            result=split_finding.result,
            details=split_finding.evidence,
            severity=split_finding.severity,
            metadata={"supporting_claims_count": len(split_finding.supporting_claims)}
        )

        # -- Check F: Near Limit Check --
        await publish_pattern_check_started(mission_id, "Spend Limit Ceiling Proximity Check")
        limit_finding = check_near_limit(current_amount, max_allowed_limit)
        findings.append(limit_finding)
        await publish_pattern_finding(
            mission_id=mission_id,
            pattern_type=limit_finding.pattern_type,
            result=limit_finding.result,
            details=limit_finding.evidence,
            severity=limit_finding.severity
        )

        # 3. Call Gemma for Behavioral Synthesis
        summary = await generate_behavioral_summary(findings)
        await publish_pattern_summary_generated(mission_id=mission_id, summary=summary)

        # 4. Resolve aggregate severity and average confidence
        aggregate_severity = Severity.SUCCESS
        status_rank = {"PASS": 0, "FLAG": 1, "HARD_FAIL": 2}
        highest_rank = 0
        
        # Standard default high confidence
        avg_confidence = 95
        confidence_sums = 0
        count_conf = 0

        for f in findings:
            rank = status_rank.get(f.result, 0)
            if rank > highest_rank:
                highest_rank = rank
                if f.result == "FLAG":
                    aggregate_severity = Severity.WARN
                elif f.result == "HARD_FAIL":
                    aggregate_severity = Severity.ERROR

            confidence_sums += f.confidence
            count_conf += 1

        if count_conf > 0:
            avg_confidence = int(confidence_sums / count_conf)

        # Short summary title
        if aggregate_severity == Severity.ERROR:
            title = "Pattern Scan: Critical Anomaly Flagged"
        elif aggregate_severity == Severity.WARN:
            title = "Pattern Scan: Warning Anomalies Found"
        else:
            title = "Pattern Scan: No Suspicious Patterns Found"

        # 5. Compile into a standard Evidence instance
        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            mission_id=mission_id,
            agent=AgentName.PATTERN,
            source="behavioral_analytics",
            title=title,
            description=summary,
            confidence=avg_confidence,
            severity=aggregate_severity,
            timestamp=datetime.now(UTC),
            metadata={
                "findings": [f.model_dump() for f in findings],
                "summary": summary,
                "historical_claims_evaluated": len(history)
            }
        )

        logger.info(f"[PATTERN ENGINE] Analysis sequence complete with aggregate state: {aggregate_severity.value}")
        return evidence


# Instantiate a singleton engine instance
pattern_evaluator = PatternEvaluator()
