"""
Module implementing the logical review consistency audit context and checks for Gemma.
Compares Arbiter decisions with specialist evidence to identify logical gaps or verify agreement.
"""

from typing import Dict, Any, Tuple
from app.core.logger import logger


def build_reviewer_context(
    decision_packet: Dict[str, Any]
) -> str:
    """
    Compiles detailed logical audit lines for the consistency review step.
    Summarizes recommendation, reasons, and specialist statuses.
    """
    audit_lines = [
        "### Logical Review Points",
        f"Target Recommendation: {decision_packet.get('recommendation', 'N/A')}",
        f"Stated Rationale: {decision_packet.get('reason', 'N/A')}"
    ]

    # Map specialist status values for analytical reasoning
    specialists = {
        "Provider Specialist": decision_packet.get("provider_evidence"),
        "Policy Specialist": decision_packet.get("policy_evidence"),
        "Pattern Specialist": decision_packet.get("pattern_evidence")
    }

    for name, ev in specialists.items():
        if ev:
            status = ev.get("status") if isinstance(ev, dict) else getattr(ev, "status", None)
            desc = ev.get("description") if isinstance(ev, dict) else getattr(ev, "description", None)
            severity = ev.get("severity") if isinstance(ev, dict) else getattr(ev, "severity", None)
            audit_lines.append(f"- {name}: status='{status}', severity='{severity}', description='{desc}'")
        else:
            audit_lines.append(f"- {name}: status='MISSING' (not executed or failed to report)")

    return "\n".join(audit_lines)


def run_procedural_consistency_check(
    decision_packet: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Procedural fallback logical review builder.
    Verifies logically if specialist statuses support the Arbiter outcome.
    - If Arbiter says APPROVE, but any specialist has error/warning: REVIEW.
    - If Arbiter says REJECT, but all specialists are SUCCESS: REVIEW.
    - If Arbiter says ESCALATE, and any specialist has warnings/conflicts: MATCH.
    """
    recommendation = decision_packet.get("recommendation", "ESCALATE").upper().strip()
    
    # Extract statuses safely
    def get_status(ev: Any) -> str:
        if not ev:
            return "MISSING"
        if isinstance(ev, dict):
            return str(ev.get("status", "success")).upper()
        return str(getattr(ev, "status", "success")).upper()

    prov_status = get_status(decision_packet.get("provider_evidence"))
    pol_status = get_status(decision_packet.get("policy_evidence"))
    patt_status = get_status(decision_packet.get("pattern_evidence"))

    has_issue = any(st in ["ERROR", "WARNING", "MISSING"] for st in [prov_status, pol_status, patt_status])

    if recommendation == "APPROVE":
        if has_issue:
            return "REVIEW", "Decision is APPROVE but specialist checks contain active warnings or missing evidence flags."
        return "MATCH", "Arbiter APPROVED status is fully consistent with clean specialist validation records."
        
    if recommendation == "REJECT":
        if not has_issue:
            return "REVIEW", "Decision is REJECT but all participating specialist checks passed successfully with green status."
        return "MATCH", "Arbiter REJECTED status matches compliance/fraud validation failures flagged by specialists."
        
    # ESCALATE
    if has_issue:
        return "MATCH", "Arbiter ESCALATE recommendation is logical because specialist checks contain unresolved warnings or anomalies."
    return "REVIEW", "Decision is ESCALATE but all specialist audits are fully successful. Escalation may be unnecessary."
