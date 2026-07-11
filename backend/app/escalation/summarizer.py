"""
Module implementing the Gemini 3.5 Flash summarization service for human escalation cases.
Leverages structured JSON outputs to generate a concise finance-oriented executive summary (< 120 words)
and exactly ONE clear, actionable question for manual claim verification.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logger import logger


class EscalationAnalysis(BaseModel):
    """
    Structured Pydantic target schema for Gemini 3.5 Flash generation.
    Ensures absolute structure guarantees for down-stream consumers.
    """
    summary: str = Field(
        description="Concise, finance-friendly executive summary under 120 words explaining what happened, why escalation occurred, and any conflicting evidence."
    )
    human_question: str = Field(
        description="Exactly ONE clear, actionable, and highly specific question for the manual reviewer. Never ask compound or vague questions."
    )


def _generate_procedural_fallback(
    claim_id: str,
    reason: str,
    provider_summary: Optional[str],
    policy_summary: Optional[str],
    pattern_summary: Optional[str]
) -> EscalationAnalysis:
    """
    Procedural fallback builder providing robust fallback objects when offline or under API errors.
    """
    logger.info(f"[ESCALATION SUMMARIZER] Running procedural fallback for Claim {claim_id}")
    
    # 1. Draft a concise fallback summary
    summary_parts = [
        f"Claim {claim_id} has been escalated for manual audit because: {reason}."
    ]
    
    anomalies = []
    if provider_summary and "fail" in provider_summary.lower() or "error" in (provider_summary or "").lower():
        anomalies.append("provider verification flags")
    if policy_summary and "limit" in policy_summary.lower() or "exception" in (policy_summary or "").lower():
        anomalies.append("corporate policy exception")
    if pattern_summary and "duplicate" in pattern_summary.lower() or "anomaly" in (pattern_summary or "").lower():
        anomalies.append("historical transaction pattern alerts")
        
    if anomalies:
        summary_parts.append(f"Adjudication highlights include {', '.join(anomalies)}.")
    else:
        summary_parts.append("Specialist validation flags require manual claim reviewer verification to proceed.")
        
    fallback_summary = " ".join(summary_parts)
    
    # 2. Draft exactly one clear question
    fallback_question = "Can you confirm the business validity and receipt details for this expense claim?"
    if "out of network" in reason.lower() or "network" in (policy_summary or "").lower():
        fallback_question = "Would you like to approve an override for this out-of-network clinic expense?"
    elif "duplicate" in (pattern_summary or "").lower() or "duplicate" in reason.lower():
        fallback_question = "Can you verify if this claim is a duplicate of a previously submitted invoice?"
    elif "provider" in (provider_summary or "").lower() or "registry" in reason.lower():
        fallback_question = "Can you verify if the provider's professional registry credentials are valid?"

    return EscalationAnalysis(
        summary=fallback_summary,
        human_question=fallback_question
    )


async def generate_escalation_analysis(
    claim_id: str,
    reason: str,
    provider_summary: Optional[str] = None,
    policy_summary: Optional[str] = None,
    pattern_summary: Optional[str] = None,
    gemma_summary: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> EscalationAnalysis:
    """
    Invokes Gemini 3.5 Flash using structured output schemas to synthesize
    specialist findings into a professional summary and review question.
    """
    # Check for missing API Key configuration
    if not settings.GEMINI_API_KEY:
        logger.warning("[ESCALATION SUMMARIZER] GEMINI_API_KEY is missing. Utilizing procedural fallback.")
        return _generate_procedural_fallback(claim_id, reason, provider_summary, policy_summary, pattern_summary)

    # 1. Assemble structured input context block (Structured Summary Builder)
    context_lines = [
        f"Claim ID: {claim_id}",
        f"Arbiter Escalation Reason: {reason}",
    ]
    if provider_summary:
        context_lines.append(f"Provider Verification Specialist Findings: {provider_summary}")
    if policy_summary:
        context_lines.append(f"Policy Auditing Specialist Findings: {policy_summary}")
    if pattern_summary:
        context_lines.append(f"Pattern Fraud Specialist Findings: {pattern_summary}")
    if gemma_summary:
        context_lines.append(f"Gemma Behavioral Synthesis Findings: {gemma_summary}")
    if metadata:
        context_lines.append(f"Audit Metadata: {metadata}")
        
    context_str = "\n".join(context_lines)

    # 2. Design System Instructions and Prompt Blocks
    system_instruction = (
        "You are the senior Escalation Summarizer for the Nexus AI Operations Platform.\n"
        "Your task is to analyze a structured report of financial/insurance claim findings and output:\n"
        "1. A professional, objective, finance-oriented executive summary of the escalation case under 120 words.\n"
        "2. Exactly ONE clear, actionable, and highly specific question for the manual reviewer to resolve.\n"
        "\n"
        "CRITICAL RULES:\n"
        "- Never use technical/internal jargon. Focus strictly on business/financial impact.\n"
        "- The executive summary must be under 120 words.\n"
        "- The reviewer question must be highly specific to the escalation context. Never ask generic, compound, or vague questions."
    )

    prompt = (
        "Analyze these structured specialist findings and generate the summary and actionable question:\n\n"
        f"{context_str}"
    )

    # 3. Call Gemini 3.5 Flash using the modern google-genai Client
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model_name = settings.MODEL_NAME or "gemini-3.5-flash"
        
        logger.info(f"[ESCALATION SUMMARIZER] Dispatching generation request to model={model_name}")
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EscalationAnalysis,
                temperature=0.2,
                max_output_tokens=500
            )
        )
        
        # Parse output safely
        if response.text:
            analysis = EscalationAnalysis.model_validate_json(response.text)
            # Extra length safety checks
            word_count = len(analysis.summary.split())
            if word_count > 120:
                logger.warning(f"[ESCALATION SUMMARIZER] Generated summary of {word_count} words exceeded 120 limit. Truncating.")
                analysis.summary = " ".join(analysis.summary.split()[:115]) + "..."
            
            logger.info("[ESCALATION SUMMARIZER] Successfully generated structured escalation package analysis.")
            return analysis
        else:
            raise ValueError("Gemini 3.5 Flash returned an empty content string.")

    except Exception as err:
        logger.error(f"[ESCALATION SUMMARIZER] Gemini API invocation failed: {err}. Falling back to procedural builder.", exc_info=True)
        return _generate_procedural_fallback(claim_id, reason, provider_summary, policy_summary, pattern_summary)
