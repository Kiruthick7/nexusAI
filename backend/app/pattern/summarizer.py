"""
Module implementing the Gemma summarization service for Pattern Agent findings.
Leverages Gemma 4 26B (via Google AI Studio) to synthesize behavioral findings into
a clean, professional executive summary. Incorporates offline, missing key, and rate limit fallbacks.
"""

from typing import List
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logger import logger
from app.pattern.models import PatternFinding


def _generate_fallback_summary(findings: List[PatternFinding]) -> str:
    """
    Generates a clean, rule-based procedural fallback summary when Gemma is unavailable.
    """
    failed_or_flagged = [f for f in findings if f.result in ("FLAG", "HARD_FAIL")]
    
    if not failed_or_flagged:
        return "No duplicate matches, split-billing anomalies, or unusual rolling transaction frequencies identified. All evaluated behavioral pattern metrics reside within standard corporate compliance ranges."

    summary_lines = []
    hard_fails = [f for f in failed_or_flagged if f.result == "HARD_FAIL"]
    flags = [f for f in failed_or_flagged if f.result == "FLAG"]
    
    if hard_fails:
        reasons = ", ".join([f.pattern_type.replace("_", " ") for f in hard_fails])
        summary_lines.append(f"CRITICAL ANOMALY: Highly suspicious transaction risk identified ({reasons}).")
    if flags:
        warnings = ", ".join([f.pattern_type.replace("_", " ") for f in flags])
        summary_lines.append(f"WARNING FLAGS: Behavioral anomalies detected ({warnings}) which require closer audit scrutiny.")

    for finding in failed_or_flagged:
        summary_lines.append(f"- [{finding.result}] {finding.evidence}")

    return "\n".join(summary_lines)


async def generate_behavioral_summary(findings: List[PatternFinding]) -> str:
    """
    Synthesizes Pattern Agent findings using the Gemma LLM from Google AI Studio.
    
    Args:
        findings: The list of evaluated PatternFinding rules.
        
    Returns:
        str: A concise, synthesized behavioral analytics summary.
    """
    # 1. Check if Gemma API is fully configured
    is_mock_mode = False
    if not settings.GEMINI_API_KEY:
        logger.warning("[GEMMA SUMMARIZER] GEMINI_API_KEY is missing from configurations. Triggering offline fallback generator.")
        is_mock_mode = True

    if is_mock_mode or not findings:
        return _generate_fallback_summary(findings)

    # 2. Format findings for prompt digestion
    findings_context = []
    for f in findings:
        findings_context.append(
            f"Pattern Type: {f.pattern_type}\n"
            f"Result: {f.result}\n"
            f"Severity: {f.severity.value}\n"
            f"Evidence: {f.evidence}\n"
            f"Confidence: {f.confidence}%\n"
            "---"
        )
    findings_str = "\n".join(findings_context)

    # 3. Create instruction block
    system_instruction = (
        "You are the high-fidelity Pattern Agent Summarizer for the Nexus AI Operations Platform.\n"
        "Your task is to analyze a structured list of behavioral/fraud finding rule evaluation outcomes, "
        "and synthesize them into a highly concise, professional executive summary.\n"
        "Keep your output clear, objective, and maximum of 2-3 sentences. Focus strictly on highlighting any "
        "reimbursement risks, duplicate billings, or billing manipulations."
    )

    prompt = (
        "Please analyze these structured behavioral findings and generate a highly concise behavioral summary. "
        "Do not output markdown code blocks or introduction/outro chatter. Return only the synthesized text summary.\n"
        "\n"
        "EVALUATED FINDINGS:\n"
        f"{findings_str}"
    )

    # 4. Invoke modern google-genai Client
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Load Gemma model name from config settings (default to gemma2-27b-it)
        model_name = settings.GEMMA_MODEL or "gemma2-27b-it"
        logger.info(f"[GEMMA SUMMARIZER] Invoking model='{model_name}' for behavioral synthesis")

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=300,
            )
        )
        
        summary_text = response.text
        if summary_text and summary_text.strip():
            logger.info("[GEMMA SUMMARIZER] Synthesis successfully generated.")
            return summary_text.strip()
        else:
            raise ValueError("Gemma returned an empty text block response.")

    except Exception as err:
        logger.error(f"[GEMMA SUMMARIZER] Synthesis failed: {str(err)}. Gracefully falling back to rule-based summary.", exc_info=True)
        return _generate_fallback_summary(findings)
