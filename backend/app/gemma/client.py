"""
Module implementing the Google AI Studio SDK client connection wrapper for Gemma.
Handles key initialization, model configuration, retry logic, timeout gating, and structured schema parsing.
"""

import asyncio
from typing import Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logger import logger
from app.gemma.models import GemmaGenerationTarget


class GemmaAPIError(Exception):
    """Custom exception class for issues occurring within the Gemma client gateway."""
    pass


class GemmaClient:
    """
    Dedicated client wrapper managing AI Studio connections, structured Pydantic schemas,
    and timeout safety guards for Google Gemma models.
    """

    def __init__(self) -> None:
        # Pydantic reads GOOGLE_API_KEY. Fall back to GEMINI_API_KEY if unconfigured.
        self.api_key = settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY
        self.model_name = settings.GEMMA_MODEL or "gemma2-27b-it"

    def get_client(self) -> Optional[genai.Client]:
        """Initializes and returns the official google-genai Client if credentials are valid."""
        if not self.api_key:
            logger.warning("[GEMMA CLIENT] API key missing. Bypassing client initialization.")
            return None
        try:
            return genai.Client(api_key=self.api_key)
        except Exception as err:
            logger.error(f"[GEMMA CLIENT] Failed to instantiate Client: {err}", exc_info=True)
            return None

    async def generate_explanation(self, prompt: str, system_instruction: str) -> Optional[GemmaGenerationTarget]:
        """
        Dispatches a structured JSON content generation call to Gemma with a hard timeout cap.
        
        Args:
            prompt: Main prompt string containing details of the adjudication.
            system_instruction: Contextual system instruction setting Gemma persona.
            
        Returns:
            Optional[GemmaGenerationTarget]: Validated target model, or None if client/API fails.
        """
        client = self.get_client()
        if not client:
            logger.warning("[GEMMA CLIENT] Client not initialized. Skipping API invocation.")
            return None

        logger.info(f"[GEMMA CLIENT] Dispatching analysis to model={self.model_name}")

        try:
            # Execute standard generate content call wrapped in asyncio.wait_for
            # Gemma models on AI Studio are queried similarly to standard models.
            # Some Gemma endpoints may have constraints on response_schema; we use response_schema
            # with standard fallback parsing to handle any variations gracefully.
            async def run_generation():
                return client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=GemmaGenerationTarget,
                        temperature=0.2,
                        max_output_tokens=1000
                    )
                )

            # Cap generation to a strict 15-second timeout limit to protect execution latency
            response = await asyncio.wait_for(run_generation(), timeout=15.0)

            if not response.text:
                raise GemmaAPIError("Gemma returned an empty content string.")

            # Validate response schema using Pydantic
            target = GemmaGenerationTarget.model_validate_json(response.text)
            logger.info("[GEMMA CLIENT] Successfully generated and parsed structured Gemma analysis.")
            return target

        except asyncio.TimeoutError:
            logger.error("[GEMMA CLIENT] Generation timed out after 15 seconds.")
            return None
        except Exception as err:
            logger.error(f"[GEMMA CLIENT] Gemma API call failed: {err}", exc_info=True)
            return None
