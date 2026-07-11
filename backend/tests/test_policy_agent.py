"""
Automated unit and integration tests verifying the Policy Audit Agent and Rule Engine.
"""

import os
import asyncio
import pytest
from datetime import datetime, date, timedelta, UTC
from app.models.enums import Severity, AgentStatus, EventType
from app.models.mission_context import SharedMissionContext
from app.policy.rules import PolicyRuleConfig, PolicyFinding
from app.policy.loader import load_policies, DEFAULT_POLICIES
from app.policy.evaluator import policy_evaluator
from app.workflow.executor import execute_agent_task
from app.core.event_bus import event_bus


def test_travel_claim_compliant():
    """
    Asserts that a fully compliant travel claim inside budget constraints is evaluated as PASS.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-101",
        claim_id="C-POL-101",
        category="Travel",
        amount=12000.0,
        currency="INR",
        invoice_number="INV-TRAVEL-101",
        vendor_name="Indigo Airlines",
        date="2026-07-01",
        gstin="07AAAAA1111A1Z1"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-101", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.SUCCESS
        assert evidence.metadata["finding"] == "COMPLIANT"
        assert evidence.metadata["hard_fail_count"] == 0
        assert evidence.metadata["flag_count"] == 0

    asyncio.run(run_test())


def test_meals_claim_exceeding_approval_threshold():
    """
    Asserts that a meals claim above standard approval thresholds triggers warnings.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-102",
        claim_id="C-POL-102",
        category="Meals",
        amount=2200.0,  # Max is 2500, but approval threshold is 2000
        currency="INR",
        invoice_number="INV-MEALS-102",
        vendor_name="Taj Dining",
        date="2026-07-02",
        gstin="07BBBBB2222B2Z2"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-102", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.WARN
        assert "exceeds approval threshold" in evidence.description
        assert evidence.metadata["flag_count"] > 0
        assert evidence.metadata["hard_fail_count"] == 0

    asyncio.run(run_test())


def test_meals_claim_exceeding_max_limit():
    """
    Asserts that a meals claim exceeding absolute limits triggers a hard failure.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-103",
        claim_id="C-POL-103",
        category="Meals",
        amount=3000.0,  # Max is 2500
        currency="INR",
        invoice_number="INV-MEALS-103",
        vendor_name="Taj Dining",
        date="2026-07-03"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-103", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.ERROR
        assert "violates guidelines" in evidence.description
        assert evidence.metadata["hard_fail_count"] > 0

    asyncio.run(run_test())


def test_cab_claim_missing_receipt_is_compliant():
    """
    Asserts that a cab claim is evaluated successfully even without physical receipt uploads.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-104",
        claim_id="C-POL-104",
        category="Cab",
        amount=800.0,  # Cab max is 1500, receipt_required is False
        currency="USD",
        vendor_name="Uber",
        date="2026-07-04"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-104", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.SUCCESS
        assert "COMPLIANT" in evidence.description or evidence.metadata["finding"] == "COMPLIANT"

    asyncio.run(run_test())


def test_office_supplies_missing_mandatory_fields():
    """
    Asserts that missing required fields inside specified categories triggers flags.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-105",
        claim_id="C-POL-105",
        category="Office Supplies",
        amount=2000.0,
        currency="USD",
        invoice_number="INV-OFFICE-105",  # satisfying receipt_required check
        vendor_name="",  # Missing required vendor name
        date="2026-07-05"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-105", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.WARN
        assert any("Missing mandatory fields" in f["details"] for f in evidence.metadata["findings"])
        assert evidence.metadata["flag_count"] > 0

    asyncio.run(run_test())


def test_unknown_category_resolves_gracefully():
    """
    Asserts that unregistered category names are mapped gracefully with safety flag checks.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-106",
        claim_id="C-POL-106",
        category="Super-Hypersonic-Jets",  # Unknown
        amount=100.0,
        currency="USD",
        vendor_name="Boeing",
        date="2026-07-06"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-106", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.WARN
        assert "Unregistered corporate category" in evidence.description

    asyncio.run(run_test())


def test_future_date_claims_rejection():
    """
    Asserts that expense dates in the future are strictly rejected.
    """
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    ctx = SharedMissionContext(
        mission_id="M-POL-107",
        claim_id="C-POL-107",
        category="Travel",
        amount=5000.0,
        currency="USD",
        vendor_name="Delta Airlines",
        date=tomorrow_str,  # Future Date
        invoice_number="INV-FUTURE-107"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-107", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.ERROR
        assert "Future date validation violation" in evidence.description

    asyncio.run(run_test())


def test_negative_amount_claims_rejection():
    """
    Asserts that negative or zero claim amounts are rejected.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-108",
        claim_id="C-POL-108",
        category="Travel",
        amount=-500.0,  # Negative
        currency="USD",
        vendor_name="Delta Airlines",
        date="2026-07-01",
        invoice_number="INV-NEG-108"
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-108", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.ERROR
        assert "must be greater than zero" in evidence.description

    asyncio.run(run_test())


def test_missing_gstin_raises_warning():
    """
    Asserts that Indian INR claims without specified GSTIN raise compliance warnings.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-109",
        claim_id="C-POL-109",
        category="Travel",
        amount=5000.0,
        currency="INR",  # INR claims require GSTIN
        vendor_name="Indigo Airlines",
        date="2026-07-01",
        invoice_number="INV-GST-109",
        gstin=""  # Missing GSTIN
    )
    
    async def run_test():
        evidence = await policy_evaluator.evaluate_claim("M-POL-109", ctx)
        assert evidence is not None
        assert evidence.severity == Severity.WARN
        assert "Indian corporate tax guidelines mandate registered vendors" in evidence.description

    asyncio.run(run_test())


def test_policy_loader_disk_resilience():
    """
    Unit test validating loader fallback capability when rules file is missing or broken.
    """
    # Load with non-existent path
    fallback_policies = load_policies("/Users/kiruthick/non_existent_policy_file.yaml")
    assert fallback_policies is not None
    assert "Travel" in fallback_policies
    assert fallback_policies["Travel"].max_amount == 20000.0


def test_policy_agent_workflow_integration():
    """
    Full end-to-end integration test of execute_agent_task calling PolicyAgent.
    """
    ctx = SharedMissionContext(
        mission_id="M-POL-INTEG-111",
        claim_id="C-POL-INTEG-111",
        category="Meals",
        amount=1500.0,  # Compliant (Limit is 2500, threshold is 2000)
        currency="INR",
        invoice_number="INV-MEAL-111",
        vendor_name="Taj Samosa",
        date="2026-07-01",
        gstin="07GSTIN1111A1Z1"
    )
    
    async def run_test():
        res = await execute_agent_task("M-POL-INTEG-111", "PolicyAgent", ctx)
        assert res is not None
        assert res["agent"] == "PolicyAgent"
        assert res["severity"] == Severity.SUCCESS
        assert "Corporate audit complete" in res["description"]

    asyncio.run(run_test())
