"""
Module declaring domain models representing the structured Execution Plan compiled by the Planner.
"""

from typing import List, Dict
from pydantic import BaseModel, Field


class ExecutionPlan(BaseModel):
    """
    Domain representation of a topologically ordered multi-agent orchestration roadmap.
    """
    mission_id: str = Field(..., description="Unique alphanumeric tracking ID of the mission.")
    participating_agents: List[str] = Field(..., description="The subset of specialist agents chosen to execute.")
    execution_order: List[str] = Field(..., description="High-level sequence ordering of execution steps/layers.")
    parallel_groups: List[List[str]] = Field(..., description="Concurrently running groups of specialist agents.")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Pre-requisite map of node names to their parent names.")
    current_status: str = Field(default="planning", description="Operational execution status state of the plan.")
