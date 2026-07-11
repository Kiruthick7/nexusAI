"""
Module implementing the Conflict Detector and Resolution Round for the Arbiter Decision Engine.
Identifies logical discrepancies between specialist findings and resolves them via structured weighting rules.
"""

import uuid
from typing import List, Dict, Any, Tuple
from app.models.evidence import Evidence
from app.models.enums import Severity, AgentName
from app.arbiter.models import Conflict, ResolutionResult
from app.core.logger import logger


class EvidenceResolver:
    """
    Scans aggregated specialist evidence to detect structural discrepancies,
    and executes exactly one structured resolution round based on reliability coefficients.
    """

    # Specialist reliability weight coefficients (must sum to 1.0)
    RELIABILITY_WEIGHTS = {
        AgentName.PROVIDER: 0.4,
        AgentName.POLICY: 0.3,
        AgentName.PATTERN: 0.3
    }

    @classmethod
    def detect_conflicts(cls, findings: List[Evidence]) -> List[Conflict]:
        """
        Analyzes findings to identify logically opposing claims or conflicting severity states.
        
        Args:
            findings: List of active Evidence objects.
            
        Returns:
            List[Conflict]: Collection of detected conflicts.
        """
        conflicts: List[Conflict] = []
        if len(findings) < 2:
            return conflicts

        logger.info("[ARBITER RESOLVER] Checking for logical conflicts across specialist evidence")

        # Create lookup map for findings
        agent_findings = {f.agent: f for f in findings}

        # Case 1: Provider matches PASS/CONFIRMED, but Pattern detects HARD_FAIL/Duplicate (Severe Risk!)
        provider = agent_findings.get(AgentName.PROVIDER)
        pattern = agent_findings.get(AgentName.PATTERN)
        policy = agent_findings.get(AgentName.POLICY)

        if provider and pattern:
            p_finding = provider.metadata.get("finding", "UNKNOWN")
            pat_finding = pattern.metadata.get("finding", "UNKNOWN")
            
            # Check for conflict: Verified ledger but anomalous behavior pattern
            if provider.severity == Severity.SUCCESS and pattern.severity == Severity.ERROR:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    severity=Severity.ERROR,
                    description=(
                        f"CRITICAL DISCREPANCY: Provider Agent verified the invoice registration ledger "
                        f"([{p_finding}] with {provider.confidence}% confidence), "
                        f"but Pattern Agent flagged the claim as an extreme risk "
                        f"([{pat_finding}] severity [{pattern.severity}]). This indicates a possible "
                        f"valid invoice being submitted fraudulently or as a duplicate attempt."
                    ),
                    conflicting_agents=[AgentName.PROVIDER.value, AgentName.PATTERN.value]
                )
                conflicts.append(conflict)
                logger.warning(f"[ARBITER RESOLVER] Critical conflict detected: {conflict.description}")

        # Case 2: Policy returns HARD_FAIL, but Provider or Pattern returns PASS
        if policy and provider:
            pol_severity = policy.severity
            prov_severity = provider.severity
            if pol_severity == Severity.ERROR and prov_severity == Severity.SUCCESS:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    severity=Severity.WARN,
                    description=(
                        f"COMPLIANCE DISCREPANCY: Claim is validated on the Provider ledger "
                        f"([{provider.title}]), but strictly fails company reimbursement limits "
                        f"([{policy.title}] with {policy.confidence}% confidence). Strict policy caps must be enforced."
                    ),
                    conflicting_agents=[AgentName.POLICY.value, AgentName.PROVIDER.value]
                )
                conflicts.append(conflict)
                logger.info(f"[ARBITER RESOLVER] Policy compliance conflict detected: {conflict.description}")

        # Case 3: Mixed Warning states with compliance flags
        if pattern and policy:
            if pattern.severity == Severity.WARN and policy.severity == Severity.SUCCESS:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    severity=Severity.WARN,
                    description=(
                        f"BEHAVIORAL WARNING: Corporate Policy audit cleared successfully ([{policy.title}]), "
                        f"but Pattern Agent triggered behavioral risk warning flags ([{pattern.title}])."
                    ),
                    conflicting_agents=[AgentName.PATTERN.value, AgentName.POLICY.value]
                )
                conflicts.append(conflict)
                logger.info(f"[ARBITER RESOLVER] Behavioral anomaly warning detected: {conflict.description}")

        return conflicts

    @classmethod
    def resolve(cls, findings: List[Evidence], conflicts: List[Conflict]) -> ResolutionResult:
        """
        Executes exactly one structured resolution round weighting evidence based on coefficients.
        
        Args:
            findings: List of active Evidence objects.
            conflicts: List of detected Conflict objects.
            
        Returns:
            ResolutionResult: Analytical resolution details.
        """
        # 1. Recalculate mathematically weighted confidence
        total_weight = 0.0
        weighted_conf_sum = 0.0
        
        for f in findings:
            weight = cls.RELIABILITY_WEIGHTS.get(f.agent, 0.3)
            total_weight += weight
            weighted_conf_sum += f.confidence * weight
            
        recalculated_confidence = 100
        if total_weight > 0:
            recalculated_confidence = int(weighted_conf_sum / total_weight)

        # Ensure confidence is clamped perfectly
        recalculated_confidence = max(0, min(100, recalculated_confidence))

        # 2. Compile resolution narrative if conflicts exist
        if not conflicts:
            return ResolutionResult(
                resolved=True,
                resolution_summary="No logical conflicts detected. All specialist guidelines align.",
                remaining_disagreement="None",
                recalculated_confidence=recalculated_confidence,
                recommended_action="PROCEED_TO_STANDARD_PROTOCOL"
            )

        logger.info(f"[ARBITER RESOLVER] Executing structured conflict resolution round for {len(conflicts)} conflicts")

        # Build analysis of the weightings
        statements = []
        for i, c in enumerate(conflicts, 1):
            statements.append(f"Discrepancy #{i}: {c.description}")

        # Determine directional resolution based on the highest severity and weights
        # Rule: Any Error/Hard fail takes absolute priority for safety, weighted towards conservative action.
        has_error_finding = any(f.severity == Severity.ERROR for f in findings)
        has_warn_finding = any(f.severity == Severity.WARN for f in findings)
        
        remaining = "None"
        if has_error_finding:
            recommended_action = "FORCE_REJECT"
            summary = (
                f"Resolution Round: Discrepancy balance resolved in favor of safety. "
                f"Specialist findings contain absolute compliance or fraud failures (Severity.ERROR). "
                f"Although certain lanes validated successfully, corporate risk protection requires "
                f"immediate rejection. Weighted Confidence computed at {recalculated_confidence}%."
            )
        elif has_warn_finding:
            recommended_action = "FORCE_ESCALATE"
            summary = (
                f"Resolution Round: Borderline compliance flags or behavioral anomalies detected (Severity.WARN). "
                f"While no single critical fail is present, the collective risk thresholds require "
                f"manual human audit clearance. Weighted Confidence computed at {recalculated_confidence}%."
            )
            remaining = "Borderline compliance anomalies need human review confirmation."
        else:
            recommended_action = "PROCEED_TO_STANDARD_PROTOCOL"
            summary = "Resolution Round: Minor disagreements resolved successfully. Confidence recalculated."

        return ResolutionResult(
            resolved=True,
            resolution_summary=summary,
            remaining_disagreement=remaining,
            recalculated_confidence=recalculated_confidence,
            recommended_action=recommended_action
        )
