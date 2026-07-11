"""
Module implementing the Planner Agent.
Coordinates overall claim orchestration, builds topological workflows,
dispatches parallel lanes, and manages life-cycle telemetry publishes.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logger import logger
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.models.enums import EventType, AgentName, AgentStatus, Severity, WorkflowStatus
from app.models.mission_context import SharedMissionContext
from app.models.execution_plan import ExecutionPlan
from app.core.event_publisher import _create_base_event, publish_agent_started, publish_agent_completed
from app.workflow.graph import WorkflowGraph
from app.workflow.dispatcher import WorkflowDispatcher


class PlannerAnalysisSchema(BaseModel):
    """
    Pydantic schema used to guarantee structured JSON output from Gemini.
    """
    participating_agents: List[str] = Field(
        ...,
        description="The subset of specialist agents to trigger, from: ['ProviderAgent', 'PolicyAgent', 'PatternAgent']."
    )
    reasoning: str = Field(..., description="Logical rationale explaining the analysis path choice.")


async def run_planner_agent(mission_id: str, claim_id: str, context: SharedMissionContext) -> ExecutionPlan:
    """
    Orchestrates the entire topological agent workflow for an expense claim mission.
    
    Args:
        mission_id: The tracking mission identifier.
        claim_id: The associated claim database ID.
        context: Compiled SharedMissionContext facts from the Intake Agent.
        
    Returns:
        ExecutionPlan: Compiled and executed workflow road-map.
    """
    logger.info(f"[PLANNER AGENT] Starting planning phase for mission_id={mission_id}")
    
    # 1. Update Mission Manager status to PLANNING
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.PLANNING)
    await mission_manager.update_stage(mission_id, "PLANNING")
    
    # 2. Publish planner_started event
    start_event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PLANNER_STARTED,
        agent=AgentName.PLANNER,
        status=AgentStatus.LOADING,
        title="Planner Agent Initialized",
        message="Analyzing shared claim context and compiling optimized topological orchestration lanes",
        severity=Severity.INFO
    )
    await event_bus.publish(start_event)
    
    # Simulate thinking delay
    await asyncio.sleep(0.5)

    # 3. Analyze claim context to choose participating agents and reasoning
    analysis = await _analyze_context_with_gemini(context)
    participating = analysis.participating_agents
    reasoning = analysis.reasoning
    
    logger.info(f"[PLANNER AGENT] Choice: {participating}. Reasoning: {reasoning}")
    
    # 4. Build the Workflow Graph
    graph = WorkflowGraph()
    
    # Always include the core PlannerAgent node as root
    graph.add_node("PlannerAgent", dependencies=[])
    
    # Add parallel specialist agent nodes with PlannerAgent as pre-requisite dependency
    for agent in participating:
        graph.add_node(agent, dependencies=["PlannerAgent"])
        
    # Get parallel groups topologically
    parallel_groups = graph.get_parallel_groups()
    
    # Standardize our ExecutionPlan
    plan = ExecutionPlan(
        mission_id=mission_id,
        participating_agents=participating,
        execution_order=["PlannerAgent", "ParallelSpecialists", "ArbiterAgent"],
        parallel_groups=[g for g in parallel_groups if "PlannerAgent" not in g],
        dependencies={agent: ["PlannerAgent"] for agent in participating},
        current_status="executing"
    )
    
    # Store the ExecutionPlan inside MissionManager
    await mission_manager.store_plan(mission_id, plan)
    
    # 5. Publish planner_dispatch event
    dispatch_event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PLANNER_DISPATCH,
        agent=AgentName.PLANNER,
        status=AgentStatus.SUCCESS,
        title="Execution Plan Dispatched",
        message=f"Dispatched parallel lanes concurrently. Choice rationale: {reasoning}",
        severity=Severity.SUCCESS,
        metadata={"plan": plan.model_dump()}
    )
    await event_bus.publish(dispatch_event)
    
    # 6. Update Mission Manager to ANALYZING stage
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ANALYZING)
    await mission_manager.update_stage(mission_id, "ANALYZING")
    
    # 7. Execute graph via WorkflowDispatcher
    dispatcher = WorkflowDispatcher(graph)
    results = await dispatcher.execute(mission_id, context)
    
    # Attach collected results as metadata to our Mission running state
    await mission_manager.attach_metadata(mission_id, {"agent_results": results})
    
    # 8. Complete Planner Phase
    plan.current_status = "completed"
    await mission_manager.store_plan(mission_id, plan)
    
    # Update Mission Manager stage to ARBITRATING (preparing hand-off to Arbiter)
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ARBITRATING)
    await mission_manager.update_stage(mission_id, "ARBITRATING")
    
    # Publish final planner_completed or workflow stage updated events (we can publish stage complete)
    complete_event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.WORKFLOW_COMPLETED,  # Let's say planner stage completed successfully
        agent=AgentName.PLANNER,
        status=AgentStatus.SUCCESS,
        title="Planner Orchestration Completed",
        message="All concurrent analysis lanes resolved successfully. Compiled evidence compiled and staged for Arbiter.",
        severity=Severity.SUCCESS,
        metadata={"results": results}
    )
    # Note: WORKFLOW_COMPLETED represents the end of this demo workflow execution step.
    await event_bus.publish(complete_event)
    
    # Finally transition Mission to COMPLETED status
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.COMPLETED)
    await mission_manager.update_stage(mission_id, "COMPLETED")
    
    logger.info(f"[PLANNER AGENT] Completed claim orchestration successfully for mission_id={mission_id}")
    return plan


async def _analyze_context_with_gemini(context: SharedMissionContext) -> PlannerAnalysisSchema:
    """
    Submits extracted facts to Gemini to choose appropriate specialist lanes.
    Falls back programmatically to a high-fidelity mock selector if the API key is not present.
    """
    # Programmatic default fallback mode
    if not settings.GEMINI_API_KEY:
        logger.warning("[PLANNER AGENT] GEMINI_API_KEY missing. Falling back to programmatic mock planning.")
        
        # High-fidelity conditional mock selection
        amount = context.amount or 0.0
        vendor = context.vendor_name or ""
        
        participating = ["ProviderAgent", "PolicyAgent", "PatternAgent"]
        reasoning = (
            f"Mock Planner fallback: Standard claim amount of {amount} from '{vendor}' "
            "requires complete validation sweeps across Provider, Policy guidelines, and historical Duplicate records."
        )
        return PlannerAnalysisSchema(participating_agents=participating, reasoning=reasoning)

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model_to_use = settings.MODEL_NAME or "gemini-3.5-flash"
        
        prompt = (
            f"You are the main Planner Agent for the Nexus AI multi-agent enterprise expense adjudication platform.\n"
            f"Your role is ONLY orchestration. Review the following extracted invoice details and select the specialist "
            f"agents that must evaluate this claim from: ['ProviderAgent', 'PolicyAgent', 'PatternAgent'].\n\n"
            f"INVOICE FACTS:\n"
            f"- Vendor: {context.vendor_name}\n"
            f"- Amount: {context.amount}\n"
            f"- Currency: {context.currency}\n"
            f"- Invoice Number: {context.invoice_number}\n"
            f"- GSTIN: {context.gstin}\n\n"
            f"CRITICAL ASSIGNMENT INSTRUCTIONS:\n"
            f"- Provide structured reasoning justifying your choices.\n"
            f"- Always execute 'ProviderAgent' if there is a vendor name.\n"
            f"- Always execute 'PolicyAgent' to verify limit guidelines.\n"
            f"- Always execute 'PatternAgent' to check duplicate invoices.\n"
        )
        
        response = client.models.generate_content(
            model=model_to_use,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PlannerAnalysisSchema
            )
        )
        
        # Parse Pydantic schema from the JSON response
        result = PlannerAnalysisSchema.model_validate_json(response.text.strip())
        return result
        
    except Exception as e:
        logger.error(f"[PLANNER AGENT] Gemini generation failed: {e}. Degrading gracefully to fallback plan.")
        return PlannerAnalysisSchema(
            participating_agents=["ProviderAgent", "PolicyAgent", "PatternAgent"],
            reasoning=f"Graceful recovery: Triggered complete validation lanes due to processing exception: {str(e)}"
        )
