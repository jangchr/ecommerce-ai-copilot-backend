import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from core.workflow import CognitiveProfile, NodeMetrics, cognitive_synthesis_node
from scripts.run_debug_tests import telemetry_node_aggregate, telemetry_rows


def synthesis_state():
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
            "audience_text": "Home-office users need dependable printing.",
            "painpoint_text": "Frequent paper jams interrupt work.",
            "dopamine_text": "relief_moment: a clean print arrives without a jam.",
        },
        "execution_state": {},
        "telemetry_state": {},
        "world_metrics": {},
        "revision_count": 0,
        "next_nodes": [],
    }


def synthesis_result():
    return CognitiveProfile(
        audience={
            "primary_user": "Home-office users",
            "anxiety_points": ["Missed deadlines"],
            "trust_barriers": ["Past paper jams"],
            "buying_motivation": "Reliable output",
        },
        painpoint={
            "physical_painpoints": ["Paper jams"],
            "emotional_painpoints": ["Work disruption"],
            "use_case_disasters": ["Document stops halfway"],
            "evidence_quotes": ["The paper jammed halfway through every print."],
        },
        dopamine={
            "relief_moment": "A clean page exits smoothly",
            "contrast_mechanism": "Jammed versus uninterrupted",
            "satisfaction_trigger": "Finished document",
            "viral_emotion": "Relief",
        },
        confidence=0.75,
        grounding_notes=[],
    )


class CognitiveSynthesisTelemetryTest(unittest.TestCase):
    def test_synthesis_records_input_and_reasoning_observability(self):
        metrics = NodeMetrics(
            total_tokens=51,
            latency_ms=18.0,
            reasoning_latency_ms=7.0,
            role_key="synthesis",
        )
        with patch(
            "core.workflow.CognitiveAgent.run",
            new=AsyncMock(return_value=(synthesis_result(), metrics)),
        ):
            result = asyncio.run(cognitive_synthesis_node(synthesis_state()))

        telemetry = result["telemetry_state"]["cognitive_synthesis"]
        self.assertEqual(telemetry["node_name"], "cognitive_synthesis")
        self.assertEqual(telemetry["total_tokens"], 51)
        self.assertEqual(telemetry["reasoning_latency_ms"], 7.0)
        self.assertGreater(telemetry["input_size_char"], 0)
        self.assertFalse(telemetry["memory_context_used"])
        self.assertEqual(telemetry["evidence_count"], 1)
        self.assertEqual(telemetry["trend_signal_count"], 1)
        self.assertFalse(telemetry["fallback"])
        self.assertEqual(telemetry["fallback_indicators"], [])
        self.assertIn("memory_retrieval_count", telemetry)
        self.assertIn("memory_backend", telemetry)

    def test_synthesis_marks_missing_analysis_inputs_as_fallback_indicators(self):
        state = synthesis_state()
        state["cognitive_state"]["dopamine_text"] = ""
        state["env_state"]["evidence"]["trend_signals"] = []
        with patch(
            "core.workflow.CognitiveAgent.run",
            new=AsyncMock(return_value=(synthesis_result(), NodeMetrics(role_key="synthesis"))),
        ):
            result = asyncio.run(cognitive_synthesis_node(state))

        telemetry = result["telemetry_state"]["cognitive_synthesis"]
        self.assertTrue(telemetry["fallback"])
        self.assertIn("no_trend_signals", telemetry["fallback_indicators"])
        self.assertIn("missing_dopamine_text", telemetry["fallback_indicators"])

    def test_reporting_projects_enriched_telemetry_to_node_aggregate(self):
        data = {
            "telemetry": {
                "cognitive_synthesis": {
                    "total_tokens": 15,
                    "latency_ms": 12,
                    "reasoning_latency_ms": 5,
                    "status": "success",
                    "node_name": "cognitive_synthesis",
                    "input_size_char": 240,
                    "memory_context_used": False,
                    "evidence_count": 2,
                    "trend_signal_count": 1,
                    "fallback": True,
                    "fallback_indicators": ["missing_dopamine_text"],
                }
            }
        }
        rows = telemetry_rows("printer", data)
        aggregate = telemetry_node_aggregate(rows)[0]

        self.assertEqual(rows[0]["reasoning_latency_ms"], 5)
        self.assertEqual(aggregate["total_input_size_char"], 240)
        self.assertEqual(aggregate["total_reasoning_latency_ms"], 5)
        self.assertEqual(aggregate["fallback_count"], 1)
        self.assertEqual(aggregate["fallback_indicators"], "missing_dopamine_text")


if __name__ == "__main__":
    unittest.main()
