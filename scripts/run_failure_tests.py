import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.workflow import RewardEngine, tool_runtime
from tests.test_reward_engine import EVIDENCE, scene


async def test_missing_dataset():
    source = await tool_runtime.run(
        "local_review_dataset",
        {
            "url": "https://test.local/products/unknown_product",
            "env_state": {"product_category": "unknown_product"},
        },
    )
    assert source.source_type == "unavailable", "unknown_product should not hit local dataset"
    assert source.items == [], "unknown_product should return no local review items"
    print("missing_dataset", {"source_type": source.source_type, "items": len(source.items)})


def test_no_evidence_alignment():
    scenes = [
        scene(1, "Invented quote that does not exist in evidence.", dopamine=False),
        scene(2, "Another invented quote that does not exist.", dopamine=True),
    ]
    metrics = RewardEngine.calculate_reward({"scenes": scenes}, EVIDENCE)
    assert metrics["failure_type"] == "no_evidence_alignment", metrics
    assert metrics["evidence_alignment"] < 0.5, metrics
    print(
        "no_evidence_alignment",
        {
            "failure_type": metrics["failure_type"],
            "evidence_alignment": metrics["evidence_alignment"],
        },
    )


def test_reward_hacking():
    scenes = [
        scene(1, EVIDENCE["evidence_quotes"][0], dopamine=True),
        scene(2, EVIDENCE["evidence_quotes"][1], dopamine=True),
        scene(3, EVIDENCE["evidence_quotes"][2], dopamine=True),
    ]
    metrics = RewardEngine.calculate_reward({"scenes": scenes}, EVIDENCE)
    assert metrics["reward_hacking_penalty"] > 0, metrics
    assert metrics["failure_type"] == "reward_hacking", metrics
    print(
        "reward_hacking",
        {
            "failure_type": metrics["failure_type"],
            "reward_hacking_penalty": metrics["reward_hacking_penalty"],
        },
    )


async def main():
    await test_missing_dataset()
    test_no_evidence_alignment()
    test_reward_hacking()


if __name__ == "__main__":
    asyncio.run(main())
