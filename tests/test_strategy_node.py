import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from core.workflow import NodeMetrics, StrategicNarrative, strategy_node


def strategy_state():
    return {
        "env_state": {
            "product_category": "printer",
            "evidence": {
                "evidence_quotes": ["The paper jammed halfway through every print."],
                "trend_signals": ["repair demo before and after"],
                "source_type": "local_dataset+mock",
                "confidence": 0.67,
                "review_confidence": 0.75,
                "trend_confidence": 0.35,
                "data_warnings": [],
            },
        },
        "cognitive_state": {
            "profile": {
                "audience": {
                    "primary_user": "Home-office users",
                    "buying_motivation": "Reliable printing",
                    "trust_barriers": ["Past jams"],
                },
                "painpoint": {
                    "physical_painpoints": ["Paper jams"],
                    "emotional_painpoints": ["Lost time"],
                },
                "dopamine": {"relief_moment": "A clean page exits smoothly"},
            }
        },
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": {},
        "revision_count": 0,
        "next_nodes": [],
    }


def strategy_result():
    return StrategicNarrative(
        target_user="Home-office users",
        core_pain="Paper jams interrupt urgent printing",
        evidence_basis=["The paper jammed halfway through every print."],
        identity_attack="A printer should not sabotage work.",
        status_desire="Look prepared and dependable.",
        future_self_gap="From stalled paperwork to clean output.",
        broken_expectation="A basic print job cannot finish.",
        visual_hook="Show the jammed sheet then a clean pass.",
        emotional_arc=["frustration", "proof", "relief"],
        trust_barrier="Users expect another jam.",
        objection_handling="Demonstrate continuous output.",
        conversion_mechanism="Proof before purchase.",
        cta_logic="Choose reliable printing.",
        risk_notes=[],
    )


class StrategyTelemetryTest(unittest.TestCase):
    def test_strategy_records_memory_and_evidence_observability(self):
        memory = {"success": ["A clean-print demonstration performed well."], "failure": []}
        metrics = NodeMetrics(
            total_tokens=44,
            latency_ms=20.0,
            reasoning_latency_ms=8.0,
            role_key="strategy",
        )
        with patch("core.workflow.memory_engine.retrieve", return_value=memory), patch(
            "core.workflow.CognitiveAgent.run",
            new=AsyncMock(return_value=(strategy_result(), metrics)),
        ):
            result = asyncio.run(strategy_node(strategy_state()))

        telemetry = result["telemetry_state"]["strategy"]
        self.assertEqual(telemetry["node_name"], "strategy")
        self.assertEqual(telemetry["total_tokens"], 44)
        self.assertEqual(telemetry["reasoning_latency_ms"], 8.0)
        self.assertGreater(telemetry["input_size_char"], 0)
        self.assertTrue(telemetry["memory_context_used"])
        self.assertEqual(telemetry["evidence_count"], 1)
        self.assertEqual(telemetry["trend_signal_count"], 1)
        self.assertFalse(telemetry["fallback"])
        self.assertIn("memory_retrieval_count", telemetry)
        self.assertIn("memory_record_count_total", telemetry)

    def test_strategy_flags_missing_memory_and_evidence_without_changing_output(self):
        state = strategy_state()
        state["env_state"]["evidence"]["evidence_quotes"] = []
        with patch("core.workflow.memory_engine.retrieve", return_value={}), patch(
            "core.workflow.CognitiveAgent.run",
            new=AsyncMock(return_value=(strategy_result(), NodeMetrics(role_key="strategy"))),
        ):
            result = asyncio.run(strategy_node(state))

        telemetry = result["telemetry_state"]["strategy"]
        self.assertTrue(telemetry["fallback"])
        self.assertIn("no_evidence_quotes", telemetry["fallback_indicators"])
        self.assertIn("no_memory_context", telemetry["fallback_indicators"])
        self.assertIn("strategy", result["cognitive_state"])


if __name__ == "__main__":
    unittest.main()
