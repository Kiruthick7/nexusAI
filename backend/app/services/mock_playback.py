"""
Module implementing the unified Mock Playback Engine coordinator.

Dispatches background simulation tasks depending on chosen scenario parameters.
"""

from app.core.logger import logger
from app.services.playback.approval import run_approval_playback
from app.services.playback.fraud import run_fraud_playback
from app.services.playback.injection import run_injection_playback
from app.services.playback.conflict import run_conflict_playback


async def run_playback_scenario(scenario_name: str, mission_id: str) -> None:
    """
    Executes a specific sequential multi-agent scenario under the target mission_id.
    
    Args:
        scenario_name: Alphanumeric scenario key (approval, fraud, injection, conflict).
        mission_id: The tracking identifier for the active session.
    """
    normalized_name = scenario_name.lower().strip()
    logger.info(f"[PLAYBACK ENGINE] Starting scenario='{normalized_name}' for mission_id='{mission_id}'")
    
    try:
        if normalized_name == "approval":
            await run_approval_playback(mission_id)
        elif normalized_name == "fraud":
            await run_fraud_playback(mission_id)
        elif normalized_name == "injection":
            await run_injection_playback(mission_id)
        elif normalized_name == "conflict":
            await run_conflict_playback(mission_id)
        else:
            logger.warning(
                f"[PLAYBACK ENGINE] Unknown scenario '{scenario_name}'. "
                f"Falling back to 'approval'."
            )
            await run_approval_playback(mission_id)
            
        logger.info(f"[PLAYBACK ENGINE] Completed scenario='{normalized_name}' for mission_id='{mission_id}'")
        
    except Exception as e:
        logger.error(
            f"[PLAYBACK ENGINE] Error during playback scenario execution: {str(e)}",
            exc_info=True
        )
