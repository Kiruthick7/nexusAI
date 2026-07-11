"""
Module responsible for compiling context and enforcing constraints for Gemma summaries.
Formats claim facts and enforces maximum word counts for executive, finance, employee, and behavioral summaries.
"""

from typing import Dict, Any, Optional
from app.core.logger import logger


def build_summaries_context(
    decision_packet: Dict[str, Any],
    metadata: Dict[str, Any]
) -> str:
    """
    Compiles raw claims data and specialist logs into structured text blocks
    to build a consistent context context for Gemma summarization tasks.
    """
    context_parts = []
    
    # Extract claim properties
    claim_id = decision_packet.get("claim_id", "N/A")
    recommendation = decision_packet.get("recommendation", "N/A")
    reason = decision_packet.get("reason", "N/A")
    confidence = decision_packet.get("confidence", "N/A")

    context_parts.append("### Claim Information")
    context_parts.append(f"Claim ID: {claim_id}")
    context_parts.append(f"Arbiter Recommendation: {recommendation}")
    context_parts.append(f"Arbiter Decision Reason: {reason}")
    context_parts.append(f"Arbiter Confidence: {confidence}%")

    # Extract specialist findings
    provider_ev = decision_packet.get("provider_evidence")
    if provider_ev:
        desc = provider_ev.get("description") if isinstance(provider_ev, dict) else getattr(provider_ev, "description", None)
        status = provider_ev.get("status") if isinstance(provider_ev, dict) else getattr(provider_ev, "status", None)
        context_parts.append(f"- Provider Specialist [{status}]: {desc}")

    policy_ev = decision_packet.get("policy_evidence")
    if policy_ev:
        desc = policy_ev.get("description") if isinstance(policy_ev, dict) else getattr(policy_ev, "description", None)
        status = policy_ev.get("status") if isinstance(policy_ev, dict) else getattr(policy_ev, "status", None)
        context_parts.append(f"- Policy Specialist [{status}]: {desc}")

    pattern_ev = decision_packet.get("pattern_evidence")
    if pattern_ev:
        desc = pattern_ev.get("description") if isinstance(pattern_ev, dict) else getattr(pattern_ev, "description", None)
        status = pattern_ev.get("status") if isinstance(pattern_ev, dict) else getattr(pattern_ev, "status", None)
        context_parts.append(f"- Pattern Specialist [{status}]: {desc}")

    # Add custom metadata (such as timestamps, OCR extraction notes)
    if metadata:
        context_parts.append("\n### Processing Metadata")
        for key, val in metadata.items():
            if isinstance(val, (str, int, float, bool)):
                context_parts.append(f"- {key}: {val}")

    return "\n".join(context_parts)


def enforce_summary_word_limits(
    behavior_summary: str,
    executive_summary: str,
    finance_summary: str,
    employee_summary: str
) -> Dict[str, str]:
    """
    Enforces the requested word limits on each generated summary to guarantee strict output safety.
    Word counts:
    - Behavioral summary: Max 80 words.
    - Executive/Finance/Employee summaries: Max 60 words.
    """
    def enforce_limit(text: str, max_words: int) -> str:
        words = text.strip().split()
        if len(words) > max_words:
            logger.warning(f"[GEMMA SUMMARIZER] Truncating summary: {len(words)} words exceeded {max_words} word limit.")
            return " ".join(words[:max_words - 1]) + "..."
        return text

    return {
        "behavior_summary": enforce_limit(behavior_summary, 80),
        "executive_summary": enforce_limit(executive_summary, 60),
        "finance_summary": enforce_limit(finance_summary, 60),
        "employee_summary": enforce_limit(employee_summary, 60)
    }
