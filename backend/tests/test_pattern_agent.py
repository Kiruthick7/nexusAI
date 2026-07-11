"""
Comprehensive unit test suite validating all Pattern Agent components.
Covers rule checks, mock loaders, Gemma API synthesis resilience, and full integration.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, UTC

from app.models.enums import Severity, AgentStatus
from app.models.mission_context import SharedMissionContext
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
from app.pattern.summarizer import generate_behavioral_summary, _generate_fallback_summary
from app.pattern.engine import pattern_evaluator


def test_loader_valid_employee_id():
    """
    Verifies that historical claims are fetched and filtered correctly for a valid employee.
    """
    async def run_test():
        matched = await load_historical_claims(employee_id="EMP-9082", current_claim_id="NEX-1003")
        # Total historical in MOCK_HISTORICAL_CLAIMS is 4. Minus current_claim_id NEX-1003 should be 3.
        assert len(matched) == 3
        assert all(c["employee_id"] == "EMP-9082" for c in matched)
        assert all(c["claim_id"] != "NEX-1003" for c in matched)
    asyncio.run(run_test())


def test_loader_missing_or_timeout():
    """
    Verifies loader gracefully handles missing parameter fields or simulated connection timeouts.
    """
    async def run_test():
        # 1. Missing employee_id
        res_empty = await load_historical_claims(employee_id=None)
        assert res_empty == []

        # 2. Simulated BigQuery Timeout
        res_timeout = await load_historical_claims(employee_id="EMP-001", simulate_timeout=True)
        assert res_timeout == []
    asyncio.run(run_test())


def test_detector_duplicate_invoice():
    """
    Validates the Duplicate Invoice detector handles clean invoices, exact matches, and collision cases.
    """
    history = [
        {
            "claim_id": "NEX-8102",
            "invoice_number": "DUP-9999",
            "amount": 4500.0,
            "currency": "INR",
            "date": "2026-07-10"
        }
    ]

    # Case 1: Completely clean invoice check
    res_clean = check_duplicate_invoice("DUP-CLEAR", 2000.0, history)
    assert res_clean.result == "PASS"
    assert res_clean.severity == Severity.SUCCESS

    # Case 2: Exact duplicate match (same invoice, same amount)
    res_dup = check_duplicate_invoice("DUP-9999", 4500.0, history)
    assert res_dup.result == "HARD_FAIL"
    assert res_dup.severity == Severity.ERROR
    assert "Duplicate transaction detected" in res_dup.evidence
    assert len(res_dup.supporting_claims) == 1

    # Case 3: Invoice hash collision (same invoice number, conflicting amount)
    res_collision = check_duplicate_invoice("DUP-9999", 1500.0, history)
    assert res_collision.result == "HARD_FAIL"
    assert res_collision.severity == Severity.ERROR
    assert "Invoice identifier reuse discrepancy detected" in res_collision.evidence


def test_detector_frequency_heuristics():
    """
    Validates rolling frequency flags submissions when rolling 7-day guidance thresholds are exceeded.
    """
    # Current date is 2026-07-11
    current_date = "2026-07-11"

    # Case 1: Normal frequency (< 3 claims in rolling window)
    history_low = [
        {"claim_id": "NEX-1", "date": "2026-07-10"},
        {"claim_id": "NEX-2", "date": "2026-07-01"}  # outside 7 days
    ]
    res_low = check_claim_frequency(current_date, history_low)
    assert res_low.result == "PASS"
    assert res_low.severity == Severity.SUCCESS

    # Case 2: Anomalous high frequency (3 in history within rolling window + 1 current = 4)
    history_high = [
        {"claim_id": "NEX-1", "date": "2026-07-10"},
        {"claim_id": "NEX-2", "date": "2026-07-09"},
        {"claim_id": "NEX-3", "date": "2026-07-08"},
    ]
    res_high = check_claim_frequency(current_date, history_high)
    assert res_high.result == "FLAG"
    assert res_high.severity == Severity.WARN
    assert "High-frequency claim anomaly" in res_high.evidence


def test_detector_same_day_vendor():
    """
    Validates that same-day duplicate entries against the same provider are correctly flagged.
    """
    history = [
        {"claim_id": "NEX-1", "date": "2026-07-11", "vendor_name": "Apex Dental"},
        {"claim_id": "NEX-2", "date": "2026-07-10", "vendor_name": "Apex Dental"}  # Different day
    ]

    # Case 1: Same day same vendor repetition
    res_flag = check_vendor_anomaly("2026-07-11", "Apex Dental", history)
    assert res_flag.result == "FLAG"
    assert res_flag.severity == Severity.WARN

    # Case 2: Different day
    res_pass = check_vendor_anomaly("2026-07-12", "Apex Dental", history)
    assert res_pass.result == "PASS"


def test_detector_weekend_submissions():
    """
    Validates weekend dates flag activities while business weekdays pass cleanly.
    """
    # 2026-07-11 is a Saturday
    res_sat = check_weekend_submission("2026-07-11")
    assert res_sat.result == "FLAG"
    assert res_sat.severity == Severity.WARN

    # 2026-07-12 is a Sunday
    res_sun = check_weekend_submission("2026-07-12")
    assert res_sun.result == "FLAG"
    assert res_sun.severity == Severity.WARN

    # 2026-07-13 is a Monday
    res_mon = check_weekend_submission("2026-07-13")
    assert res_mon.result == "PASS"
    assert res_mon.severity == Severity.SUCCESS


def test_detector_split_billing():
    """
    Validates split billing detection.
    """
    history = [
        {"claim_id": "NEX-1", "date": "2026-07-11", "vendor_name": "Apex Dental", "category": "Meals", "amount": 2000.0}
    ]

    # Case 1: Combined exceeds max_amount (Meals limit is 2500.0)
    res_violation = check_split_billing(
        current_date_str="2026-07-11",
        current_vendor="Apex Dental",
        current_amount=1500.0,
        current_category="Meals",
        history=history,
        max_amount=2500.0
    )
    assert res_violation.result == "HARD_FAIL"
    assert res_violation.severity == Severity.ERROR
    assert "Split-billing violation flagged" in res_violation.evidence

    # Case 2: Combined stays under max_amount
    res_compliant = check_split_billing(
        current_date_str="2026-07-11",
        current_vendor="Apex Dental",
        current_amount=300.0,
        current_category="Meals",
        history=history,
        max_amount=2500.0
    )
    assert res_compliant.result == "PASS"


def test_detector_near_limit():
    """
    Validates that claims coming within 95%-100% of limits trigger warnings.
    """
    # Meal single reimbursement limit = 2500
    # 95% of 2500 = 2375

    # Case 1: Exactly clean (80%)
    res_clean = check_near_limit(1800.0, 2500.0)
    assert res_clean.result == "PASS"

    # Case 2: Warning zone (98%)
    res_warn = check_near_limit(2450.0, 2500.0)
    assert res_warn.result == "FLAG"
    assert res_warn.severity == Severity.WARN


def test_fallback_summarizer():
    """
    Verifies rule-based backup summarization matches expected formatting guidelines.
    """
    findings = [
        PatternFinding(
            pattern_type="weekend_activity",
            severity=Severity.WARN,
            result="FLAG",
            evidence="Anomalous submission made on Saturday"
        ),
        PatternFinding(
            pattern_type="duplicate_invoice",
            severity=Severity.ERROR,
            result="HARD_FAIL",
            evidence="Exact duplicate claim NEX-8102 identified in records"
        )
    ]

    summary = _generate_fallback_summary(findings)
    assert "CRITICAL ANOMALY: Highly suspicious transaction risk identified (duplicate invoice)" in summary
    assert "WARNING FLAGS: Behavioral anomalies detected (weekend activity)" in summary
    assert "- [HARD_FAIL] Exact duplicate claim NEX-8102" in summary


@patch("app.pattern.summarizer.genai.Client")
def test_gemma_api_summarizer_success(mock_client_class):
    """
    Verifies that the Gemma summarizer interacts with Google GenAI SDK successfully under nominal settings.
    """
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Configure mock LLM response
    mock_resp = MagicMock()
    mock_resp.text = "This is a synthesized high-fidelity summary of behavioral patterns."
    mock_client.models.generate_content.return_value = mock_resp

    findings = [
        PatternFinding(
            pattern_type="near_limit_activity",
            severity=Severity.WARN,
            result="FLAG",
            evidence="Claim sits in warning zone."
        )
    ]

    # Patch settings to ensure API Key is present for mock test
    with patch("app.pattern.summarizer.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "mock-key"
        mock_settings.GEMMA_MODEL = "gemma2-27b-it"
        
        async def run_test():
            summary = await generate_behavioral_summary(findings)
            assert summary == "This is a synthesized high-fidelity summary of behavioral patterns."
            mock_client.models.generate_content.assert_called_once()
        asyncio.run(run_test())


@patch("app.pattern.engine.load_historical_claims")
@patch("app.pattern.engine.publish_pattern_history_loaded")
@patch("app.pattern.engine.publish_pattern_check_started")
@patch("app.pattern.engine.publish_pattern_finding")
@patch("app.pattern.engine.publish_pattern_summary_generated")
def test_engine_integration_pipeline(
    mock_summary_pub,
    mock_finding_pub,
    mock_check_pub,
    mock_loaded_pub,
    mock_claims_loader
):
    """
    Validates end-to-end Pattern Engine flow execution and progress streaming triggers.
    """
    # Mock mocks
    mock_claims_loader.return_value = []
    mock_loaded_pub.return_value = AsyncMock()
    mock_check_pub.return_value = AsyncMock()
    mock_finding_pub.return_value = AsyncMock()
    mock_summary_pub.return_value = AsyncMock()

    context = SharedMissionContext(
        mission_id="RUN-99",
        claim_id="NEX-99",
        employee_id="EMP-9082",
        amount=2450.0,  # 98% of Meals category limit (2500)
        currency="INR",
        category="Meals",
        invoice_number="INV-SAFE-123",
        vendor_name="Precision Dental",
        date="2026-07-11"  # Weekend
    )

    # Execute complete engine scan
    with patch("app.pattern.engine.generate_behavioral_summary", return_value="Integrated test summary text") as mock_gen_sum:
        async def run_test():
            evidence = await pattern_evaluator.evaluate_patterns("RUN-99", context)
            
            assert evidence.mission_id == "RUN-99"
            assert evidence.source == "behavioral_analytics"
            assert evidence.severity == Severity.WARN  # Weekend + near limit flags
            assert "Warning" in evidence.title
            assert len(evidence.metadata["findings"]) == 6
            
            # Verify checkpoint event emission counts
            assert mock_loaded_pub.call_count == 1
            assert mock_check_pub.call_count == 6
            assert mock_finding_pub.call_count == 6
            assert mock_summary_pub.call_count == 1
        asyncio.run(run_test())
