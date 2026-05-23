import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.workflow import (
    RewardEngine,
    failure_to_regenerate_node,
    governance_router,
    reflection_router,
    tool_runtime,
)
from tests.test_reward_engine import EVIDENCE, scene


def assert_route(metrics, expected_node):
    state = {
        "env_state": {},
        "cognitive_state": {},
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": metrics,
        "revision_count": 0,
        "next_nodes": [],
    }
    assert governance_router(state) == "reflection", metrics
    regenerate_node = failure_to_regenerate_node(metrics)
    assert regenerate_node == expected_node, metrics
    state["execution_state"]["regenerate_node"] = regenerate_node
    assert reflection_router(state) == expected_node, metrics


async def test_unknown_product_routes_to_retrieval():
    source = await tool_runtime.run(
        "local_review_dataset",
        {
            "url": "https://test.local/products/unknown_product",
            "env_state": {"product_category": "unknown_product"},
        },
    )
    assert source.source_type == "unavailable"
    metrics = {
        "is_approved": True,
        "is_grounded": False,
        "failure_type": "low_source_confidence",
    }
    assert_route(metrics, "retrieval")
    print("unknown_product_route", {"failure_type": "low_source_confidence", "regenerate_node": "retrieval"})


def test_no_evidence_alignment_routes_to_storyboard():
    metrics = RewardEngine.calculate_reward(
        {
            "scenes": [
                scene(1, "Invented quote not in evidence.", dopamine=False),
                scene(2, "Another invented quote not in evidence.", dopamine=True),
            ]
        },
        EVIDENCE,
    )
    assert metrics["failure_type"] == "no_evidence_alignment", metrics
    assert_route(metrics, "storyboard")
    print("no_evidence_alignment_route", {"failure_type": metrics["failure_type"], "regenerate_node": "storyboard"})


def test_reward_hacking_routes_to_storyboard():
    metrics = RewardEngine.calculate_reward(
        {
            "scenes": [
                scene(1, EVIDENCE["evidence_quotes"][0], dopamine=True),
                scene(2, EVIDENCE["evidence_quotes"][1], dopamine=True),
                scene(3, EVIDENCE["evidence_quotes"][2], dopamine=True),
            ]
        },
        EVIDENCE,
    )
    assert metrics["failure_type"] == "reward_hacking", metrics
    assert_route(metrics, "storyboard")
    print("reward_hacking_route", {"failure_type": metrics["failure_type"], "regenerate_node": "storyboard"})


def test_weak_visual_routes_to_storyboard():
    metrics = RewardEngine.calculate_reward(
        {
            "scenes": [
                {
                    **scene(1, EVIDENCE["evidence_quotes"][0], dopamine=False),
                    "visual_description": "Too short.",
                }
            ]
        },
        EVIDENCE,
    )
    assert metrics["failure_type"] == "weak_visual", metrics
    assert_route(metrics, "storyboard")
    print("weak_visual_route", {"failure_type": metrics["failure_type"], "regenerate_node": "storyboard"})


async def main():
    await test_unknown_product_routes_to_retrieval()
    test_no_evidence_alignment_routes_to_storyboard()
    test_reward_hacking_routes_to_storyboard()
    test_weak_visual_routes_to_storyboard()


if __name__ == "__main__":
    asyncio.run(main())
