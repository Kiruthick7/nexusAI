"""
Module implementing the thread-safe, in-memory Mission Manager database mock.

Handles creation, stage updates, workflow status changes, metadata enrichment,
and retrieval of active Mission states.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.models.mission import Mission
from app.models.enums import WorkflowStatus
from app.core.logger import logger


class MissionManager:
    """
    In-memory registry managing the complete lifecycle state-machine of active running missions.
    """
    def __init__(self) -> None:
        self._missions: Dict[str, Mission] = {}
        self._lock = asyncio.Lock()

    async def create_mission(self, mission_id: str, claim_id: str, metadata: Optional[Dict[str, Any]] = None) -> Mission:
        """
        Creates and registers a new Mission instance initialized in the IDLE state.
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            mission = Mission(
                mission_id=mission_id,
                claim_id=claim_id,
                workflow_status=WorkflowStatus.IDLE,
                current_stage="IDLE",
                created_at=now,
                updated_at=now,
                metadata=metadata or {}
            )
            self._missions[mission_id] = mission
            logger.info(f"[MISSION MANAGER] Created mission_id={mission_id} matching claim_id={claim_id}")
            return mission

    async def get_mission(self, mission_id: str) -> Optional[Mission]:
        """
        Retrieves a registered Mission instance by its tracking identifier.
        """
        async with self._lock:
            return self._missions.get(mission_id)

    async def update_stage(self, mission_id: str, current_stage: str) -> Optional[Mission]:
        """
        Updates the active execution stage label of a running mission.
        """
        async with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                logger.warning(f"[MISSION MANAGER] Attempted stage update on missing mission_id={mission_id}")
                return None
            
            mission.current_stage = current_stage
            mission.updated_at = datetime.now(timezone.utc)
            logger.info(f"[MISSION MANAGER] Updated stage of mission_id={mission_id} to '{current_stage}'")
            return mission

    async def update_workflow_status(self, mission_id: str, status: WorkflowStatus) -> Optional[Mission]:
        """
        Transitions the high-level workflow phase status of a mission.
        """
        async with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                logger.warning(f"[MISSION MANAGER] Attempted status update on missing mission_id={mission_id}")
                return None
            
            mission.workflow_status = status
            mission.updated_at = datetime.now(timezone.utc)
            logger.info(f"[MISSION MANAGER] Transitioned status of mission_id={mission_id} to '{status.value}'")
            return mission

    async def attach_metadata(self, mission_id: str, metadata: Dict[str, Any]) -> Optional[Mission]:
        """
        Enriches a mission metadata state by merging key-value parameters.
        """
        async with self._lock:
            mission = self._missions.get(mission_id)
            if not mission:
                logger.warning(f"[MISSION MANAGER] Attempted metadata enrichment on missing mission_id={mission_id}")
                return None
            
            mission.metadata.update(metadata)
            mission.updated_at = datetime.now(timezone.utc)
            logger.debug(f"[MISSION MANAGER] Attached metadata parameters to mission_id={mission_id}")
            return mission

    async def clear_mission(self, mission_id: str) -> None:
        """
        Deregisters a mission session from active memory.
        """
        async with self._lock:
            if mission_id in self._missions:
                del self._missions[mission_id]
                logger.debug(f"[MISSION MANAGER] Deregistered mission_id={mission_id}")


# Instantiate a global singleton Mission Manager
mission_manager = MissionManager()
