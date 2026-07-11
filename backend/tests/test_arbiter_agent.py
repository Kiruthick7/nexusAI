"""
Unit and integration tests for the Arbiter Decision Engine.
Verifies standard decisions (APPROVE, REJECT, ESCALATE), conflict resolution rounds,
resiliency with missing specialist inputs, and Tool Gate integration.
"""

import pytest
import uuid
from datetime import datetime, UTC
from app.models.enums import AgentName, Severity, EventType
from app.models.evidence import Evidence
from app.models.evidence_bundle import EvidenceBundle
from app.arbiter.decision_engine import ArbiterDecisionEngine
from app.gates import evaluate_gate_check


@pytest.fixture
def base_evidence_args():
    return {
        "mission_id": "test-mission-123",
        "source": "mock_worker",
        "timestamp": datetime.now(UTC),
        "metadata": {}
    }


@pytest.mark.anyio
async def test_arbiter_all_pass_recommends_approve(base_evidence_args):
    """
    Test that when all specialist agents return SUCCESS, the Arbiter recommends APPROVE.
    """
    prov = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PROVIDER,
        title="Ledger Confirmed",
        description="Invoice found registered on provider ledger.",
        confidence=95,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )
    pol = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.POLICY,
        title="Policy Limit OK",
        description="Claim is below limit guidelines.",
        confidence=100,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )
    pat = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PATTERN,
        title="No Behavior Anomaly",
        description="Claim frequency matches clean historical baseline.",
        confidence=90,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )

    bundle = EvidenceBundle(
        mission_id="test-mission-123",
        provider_findings=prov,
        policy_findings=pol,
        pattern_findings=pat
    )

    packet = await ArbiterDecisionEngine.evaluate_bundle(bundle)

    assert packet.recommendation == "APPROVE"
    assert "approve" in packet.reason.lower()
    assert packet.confidence > 90
    assert len(packet.conflicts) == 0
    assert packet.human_question is None
    assert packet.audit_summary["is_complete"] is True
    assert packet.audit_summary["conflict_count"] == 0


@pytest.mark.anyio
async def test_arbiter_provider_error_recommends_reject(base_evidence_args):
    """
    Test that a severe Provider ledger failure (Severity.ERROR) results in a REJECT recommendation.
    """
    prov = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PROVIDER,
        title="Invoice Not Found",
        description="Invoice does not exist in vendor record database.",
        confidence=100,
        severity=Severity.ERROR,
        **base_evidence_args
    )
    pol = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.POLICY,
        title="Policy Limit OK",
        description="Claim is below limit guidelines.",
        confidence=100,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )
    pat = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PATTERN,
        title="No Behavior Anomaly",
        description="No anomalies found.",
        confidence=90,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )

    bundle = EvidenceBundle(
        mission_id="test-mission-123",
        provider_findings=prov,
        policy_findings=pol,
        pattern_findings=pat
    )

    packet = await ArbiterDecisionEngine.evaluate_bundle(bundle)

    assert packet.recommendation == "REJECT"
    assert "reject" in packet.reason.lower()
    assert len(packet.conflicts) == 0


@pytest.mark.anyio
async def test_arbiter_policy_error_recommends_reject(base_evidence_args):
    """
    Test that a severe Policy compliance failure (Severity.ERROR) results in a REJECT recommendation.
    """
    prov = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PROVIDER,
        title="Ledger Confirmed",
        description="Invoice found registered.",
        confidence=95,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )
    pol = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.POLICY,
        title="Excessive Spending Limit Breach",
        description="Expense exceeds maximum individual limit by 500%.",
        confidence=100,
        severity=Severity.ERROR,
        **base_evidence_args
    )
    pat = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PATTERN,
        title="No Behavior Anomaly",
        description="No anomalies found.",
        confidence=90,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )

    bundle = EvidenceBundle(
        mission_id="test-mission-123",
        provider_findings=prov,
        policy_findings=pol,
        pattern_findings=pat
    )

    packet = await ArbiterDecisionEngine.evaluate_bundle(bundle)

    assert packet.recommendation == "REJECT"
    assert "reject" in packet.reason.lower()


@pytest.mark.anyio
async def test_arbiter_pattern_warn_recommends_escalate(base_evidence_args):
    """
    Test that a warning indicator (Severity.WARN) from the Pattern Agent escalates the claim.
    """
    prov = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PROVIDER,
        title="Ledger Confirmed",
        description="Invoice found registered.",
        confidence=95,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )
    pol = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.POLICY,
        title="Policy Limit OK",
        description="Claim is below limit guidelines.",
        confidence=100,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )
    pat = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PATTERN,
        title="Split-Billing Indicator",
        description="User filed three identical claims within 5 hours.",
        confidence=75,
        severity=Severity.WARN,
        **base_evidence_args
    )

    bundle = EvidenceBundle(
        mission_id="test-mission-123",
        provider_findings=prov,
        policy_findings=pol,
        pattern_findings=pat
    )

    packet = await ArbiterDecisionEngine.evaluate_bundle(bundle)

    assert packet.recommendation == "ESCALATE"
    assert "escalate" in packet.reason.lower()
    assert packet.human_question is not None
    assert "Split-Billing Indicator" in packet.human_question
    assert "### 📋 Case Review Summary" in packet.human_question


@pytest.mark.anyio
async def test_arbiter_conflict_resolution_forced_reject(base_evidence_args):
    """
    Tests conflict detection and resolution logic.
    A conflict where Provider=SUCCESS but Pattern=ERROR (e.g. verified ledger but duplicate attempt)
    triggers a conflict and forces a REJECT resolution outcome.
    """
    prov = Evidence(
        evidence_id=str(uuid.uuid4()),
        mission_id="test-mission-conflict-123",
        agent=AgentName.PROVIDER,
        source="mock_worker",
        title="Ledger Verified",
        description="Invoice found in official records.",
        confidence=95,
        severity=Severity.SUCCESS,
        timestamp=datetime.now(UTC),
        metadata={"finding": "CONFIRMED"}
    )
    pol = Evidence(
        evidence_id=str(uuid.uuid4()),
        mission_id="test-mission-conflict-123",
        agent=AgentName.POLICY,
        source="mock_worker",
        title="Policy Limit OK",
        description="Claim below limit.",
        confidence=100,
        severity=Severity.SUCCESS,
        timestamp=datetime.now(UTC)
    )
    pat = Evidence(
        evidence_id=str(uuid.uuid4()),
        mission_id="test-mission-conflict-123",
        agent=AgentName.PATTERN,
        source="mock_worker",
        title="Duplicate Invoice Risk Detected",
        description="Invoice ID matches a claim processed 2 days ago.",
        confidence=90,
        severity=Severity.ERROR,
        timestamp=datetime.now(UTC),
        metadata={"finding": "HARD_FAIL"}
    )

    bundle = EvidenceBundle(
        mission_id="test-mission-conflict-123",
        provider_findings=prov,
        policy_findings=pol,
        pattern_findings=pat
    )

    packet = await ArbiterDecisionEngine.evaluate_bundle(bundle)

    assert len(packet.conflicts) == 1
    assert "CRITICAL DISCREPANCY" in packet.conflicts[0]["description"]
    assert packet.recommendation == "REJECT"
    assert "rejection" in packet.audit_summary["weighted_resolution_summary"].lower()


@pytest.mark.anyio
async def test_arbiter_resilient_to_missing_evidence(base_evidence_args):
    """
    Test that the Arbiter does not crash when specialist findings are missing.
    Incomplete data gets escalated cleanly with structured warnings.
    """
    prov = Evidence(
        evidence_id=str(uuid.uuid4()),
        agent=AgentName.PROVIDER,
        title="Ledger Verified",
        description="Invoice found registered on ledger.",
        confidence=95,
        severity=Severity.SUCCESS,
        **base_evidence_args
    )

    # Missing Policy and Pattern findings entirely
    bundle = EvidenceBundle(
        mission_id="test-mission-incomplete-123",
        provider_findings=prov,
        policy_findings=None,
        pattern_findings=None
    )

    packet = await ArbiterDecisionEngine.evaluate_bundle(bundle)

    assert packet.recommendation == "ESCALATE"
    assert "missing" in packet.reason.lower()
    assert packet.audit_summary["is_complete"] is False
    assert "PolicyAgent" in packet.audit_summary["missing_specialists"]
    assert "PatternAgent" in packet.audit_summary["missing_specialists"]
