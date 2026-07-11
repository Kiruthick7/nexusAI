"""
Module implementing the topological workflow dependency graph representation.
Ensures specialist tasks are scheduled in correctly ordered parallel execution layers without cycles.
"""

from typing import List, Dict, Set


class WorkflowNode:
    """
    Represents a single execution agent task node within the workflow graph.
    """
    def __init__(self, name: str, dependencies: List[str] = None) -> None:
        self.name = name
        self.dependencies = dependencies or []


class WorkflowGraph:
    """
    Logical topological dependency map containing workflow execution nodes.
    """
    def __init__(self) -> None:
        self.nodes: Dict[str, WorkflowNode] = {}

    def add_node(self, name: str, dependencies: List[str] = None) -> None:
        """
        Registers a task node and its prerequisite parent node names.
        """
        self.nodes[name] = WorkflowNode(name, dependencies)

    def get_parallel_groups(self) -> List[List[str]]:
        """
        Performs a Kahn-style topological sort to group nodes into concurrently executable layers.
        
        Raises:
            ValueError: If a dependency cycle is detected.
        """
        # Track in-degrees and copy graph structure
        in_degree: Dict[str, int] = {name: 0 for name in self.nodes}
        adj_list: Dict[str, Set[str]] = {name: set() for name in self.nodes}

        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    adj_list[dep].add(name)
                    in_degree[name] += 1
                else:
                    # External dependency ignored or assumed already complete
                    pass

        # Find nodes with 0 in-degree (initial layer)
        current_layer = [name for name, degree in in_degree.items() if degree == 0]
        parallel_groups: List[List[str]] = []

        visited_count = 0

        while current_layer:
            # Add this layer of independent tasks
            parallel_groups.append(sorted(current_layer))
            visited_count += len(current_layer)
            
            next_layer = []
            for u in current_layer:
                for v in adj_list[u]:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        next_layer.append(v)
            current_layer = next_layer

        if visited_count != len(self.nodes):
            raise ValueError("Topological Sort Failed: Circular dependency detected in the workflow graph!")

        return parallel_groups
