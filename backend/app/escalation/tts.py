"""
Module implementing the Gemini 3.1 Flash Text-to-Speech preview integration.
Synthesizes spoken audio briefs detailing the escalation decision, reason, and actionable question,
ensuring graceful degradation and logging under preview exceptions or rate limits.
"""

from typing import Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logger import logger


async def synthesize_briefing_audio(
    claim_id: str,
    decision_reason: str,
    question: str
) -> Optional[bytes]:
    """
    Synthesizes a short spoken voice brief (10-15s duration) detailing the decision,
    reason, and review question using gemini-3.1-flash-tts-preview.
    
    Args:
        claim_id: Alphanumeric claim tracking ID.
        decision_reason: Arbiter escalation rationale.
        question: Single actionable review question.
        
    Returns:
        Optional[bytes]: Raw .wav binary audio data if synthesis succeeds, or None if failed.
    """
    # 1. Draft the high-clarity conversational spoken script (~30 words)
    # Keeping it conversational ensures natural phrasing and predictable timing.
    spoken_script = (
        f"Claim {claim_id} requires manual audit. "
        f"Reason: {decision_reason}. "
        f"Auditor review question: {question}"
    )
    
    word_count = len(spoken_script.split())
    logger.info(f"[TTS SERVICE] Prepared spoken briefing script ({word_count} words): '{spoken_script}'")

    # 2. Check if Gemini API credentials exist
    if not settings.GEMINI_API_KEY:
        logger.warning("[TTS SERVICE] GEMINI_API_KEY is missing from configuration settings. Gracefully bypassing TTS synthesis.")
        return None

    # 3. Call the Gemini 3.1 Flash Text-to-Speech model
    # Model name is configured from settings.MODEL_NAME_TTS or falls back to 'gemini-3.1-flash-tts-preview'
    model_name = settings.MODEL_NAME_TTS or "gemini-3.1-flash-tts-preview"
    logger.info(f"[TTS SERVICE] Invoking model='{model_name}' for voice synthesis.")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # We specify response_modalities=["AUDIO"] and Kore voice config
        response = client.models.generate_content(
            model=model_name,
            contents=f"Please read the following briefing clearly, at a standard pace: {spoken_script}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore'
                        )
                    )
                ),
                temperature=0.3
            )
        )
        
        # 4. Safely extract and validate inline binary data
        if not response.candidates or not response.candidates[0].content.parts:
            raise ValueError("TTS API response candidate structure is empty.")
            
        audio_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                audio_part = part
                break
                
        if audio_part:
            logger.info("[TTS SERVICE] Text-to-Speech synthesis successfully completed.")
            return audio_part.inline_data.data
        else:
            raise ValueError("No binary inline audio data found in the response parts.")

    except Exception as err:
        # Gracefully degrade and log. Never crash the claim processing pipeline because of TTS.
        logger.error(
            f"[TTS SERVICE] Failed to synthesize briefing audio using {model_name}: {err}. "
            f"Continuing claim escalation with audio_url=null.",
            exc_info=True
        )
        return None
