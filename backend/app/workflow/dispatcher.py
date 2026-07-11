"""
Module implementing the scheduling and dispatching of workflow graph execution steps.
Resolves sequential layers step-by-step, while dispatching parallel lanes concurrently.
"""

import asyncio
from typing import List, Dict, Any
from app.workflow.graph import WorkflowGraph
from app.workflow.executor import execute_agent_task
from app.models.mission_context import SharedMissionContext
from app.core.logger import logger


class WorkflowDispatcher:
    """
    Schedules and coordinates the execution of tasks inside a WorkflowGraph.
    """
    def __init__(self, graph: WorkflowGraph) -> None:
        self.graph = graph

    async def execute(self, mission_id: str, context: SharedMissionContext) -> Dict[str, Dict[str, Any]]:
        """
        Runs the workflow graph step-by-step by resolving parallel layers concurrently.
        
        Args:
            mission_id: The active running mission identifier.
            context: The extracted SharedMissionContext facts.
            
        Returns:
            Dict: Dictionary mapping agent name strings to their compiled result dicts.
        """
        # Get parallel groups grouped topologically (Kahn sort)
        layers = self.graph.get_parallel_groups()
        logger.info(f"[DISPATCHER] Starting workflow execution for mission_id={mission_id} with {len(layers)} topological layers.")
        
        workflow_results: Dict[str, Dict[str, Any]] = {}

        for index, layer in enumerate(layers):
            logger.info(f"[DISPATCHER] Dispatching layer {index + 1}/{len(layers)}: nodes={layer}")
            
            # Form concurrent asyncio tasks for nodes in the same parallel group layer
            tasks = []
            for node_name in layer:
                # We skip 'PlannerAgent' or 'ArbiterAgent' from parallel executor simulation,
                # since Planner runs outside this loop and Arbiter executes after.
                if node_name in ["PlannerAgent", "ArbiterAgent"]:
                    continue
                tasks.append(execute_agent_task(mission_id, node_name, context))
            
            if tasks:
                # Concurrently execute all parallel lanes in this layer
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for node_name, res in zip([n for n in layer if n not in ["PlannerAgent", "ArbiterAgent"]], results):
                    if isinstance(res, Exception):
                        logger.error(f"[DISPATCHER] Layer {index + 1} node '{node_name}' execution failed: {res}")
                        workflow_results[node_name] = {
                            "agent_name": node_name,
                            "status": "error",
                            "severity": "ERROR",
                            "message": f"Execution error: {str(res)}",
                            "confidence": 0,
                            "latency_ms": 0,
                            "metadata": {"error": str(res)}
                        }
                    else:
                        workflow_results[node_name] = res
            else:
                logger.debug(f"[DISPATCHER] Layer {index + 1} has no simulated parallel worker tasks.")
                
        logger.info(f"[DISPATCHER] Completed workflow execution for mission_id={mission_id}.")
        return workflow_results
