from typing import Any


def summarize_telemetry(telemetry_state: dict) -> dict[str, Any]:
    metrics_by_node = telemetry_state if isinstance(telemetry_state, dict) else {}
    total_tokens = 0
    total_latency_ms = 0.0
    failed_nodes: list[str] = []
    max_latency_node = None
    max_token_node = None
    max_latency = -1.0
    max_tokens = -1

    for node_name, metrics in metrics_by_node.items():
        if not isinstance(metrics, dict):
            continue
        tokens = int(metrics.get("total_tokens", 0) or 0)
        latency = float(metrics.get("latency_ms", 0.0) or 0.0)
        status = metrics.get("status", "success")

        total_tokens += tokens
        total_latency_ms += latency
        if status != "success":
            failed_nodes.append(node_name)
        if latency > max_latency:
            max_latency = latency
            max_latency_node = node_name
        if tokens > max_tokens:
            max_tokens = tokens
            max_token_node = node_name

    return {
        "node_count": len(metrics_by_node),
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency_ms,
        "failed_nodes": failed_nodes,
        "max_latency_node": max_latency_node,
        "max_token_node": max_token_node,
    }
