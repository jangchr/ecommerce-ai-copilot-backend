from typing import Any, Dict, List, TypedDict


class GraphState(TypedDict):
    env_state: Dict[str, Any]
    cognitive_state: Dict[str, Any]
    execution_state: Dict[str, Any]
    telemetry_state: Dict[str, dict]
    world_metrics: Dict[str, Any]
    revision_count: int
    next_nodes: List[str]
