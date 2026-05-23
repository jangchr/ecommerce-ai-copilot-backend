import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from core.workflow import FaissMemoryEngine, NodeMetrics, analytics_node, parallel_analysis_node
from scripts.run_debug_tests import telemetry_node_aggregate, telemetry_rows


class MemoryBucketTest(unittest.TestCase):
    def setUp(self):
        self.engine = FaissMemoryEngine()

    def test_creative_pass_but_not_grounded_goes_to_failure(self):
        record = {
            "predicted_ctr": 0.09,
            "reward_metrics": {
                "is_approved": True,
                "is_grounded": False,
                "grounded_ctr": 0.02,
            },
        }
        self.assertEqual(self.engine._memory_bucket_for_record(record), "failure")

    def test_grounded_approved_result_goes_to_success(self):
        record = {
            "predicted_ctr": 0.08,
            "reward_metrics": {
                "is_approved": True,
                "is_grounded": True,
                "grounded_ctr": 0.05,
            },
        }
        self.assertEqual(self.engine._memory_bucket_for_record(record), "success")

    def test_grounded_ctr_below_threshold_goes_to_failure(self):
        record = {
            "predicted_ctr": 0.08,
            "reward_metrics": {
                "is_approved": True,
                "is_grounded": True,
                "grounded_ctr": 0.039,
            },
        }
        self.assertEqual(self.engine._memory_bucket_for_record(record), "failure")

    def test_observability_tracks_write_skip_and_json_retrieval(self):
        self.engine.records = {"success": [], "failure": []}
        record = {
            "product_type": "printer",
            "strategy": {"core_pain": "paper jam"},
            "reward_metrics": {
                "is_approved": True,
                "is_grounded": True,
                "grounded_ctr": 0.05,
                "predicted_ctr": 0.07,
            },
        }
        with patch.object(self.engine, "_persist_records"), patch.object(
            self.engine, "_ensure_faiss", return_value=False
        ):
            self.engine.save_memory(record.copy())
            self.engine.save_memory(record.copy())
            result = self.engine.retrieve("printer", k=1)

        snapshot = self.engine.observability_snapshot()
        self.assertEqual(snapshot["write_count"], 1)
        self.assertEqual(snapshot["skipped_count"], 1)
        self.assertEqual(snapshot["retrieval_count"], 1)
        self.assertEqual(snapshot["retrieval_hits"]["success"], len(result["success"]))
        self.assertEqual(snapshot["backend"], "json_fallback")
        self.assertEqual(snapshot["memory_record_count"]["success"], 1)
        self.assertEqual(snapshot["memory_growth"]["max_record_count"], self.engine.max_record_count)

    def test_memory_growth_limit_prunes_oldest_record_in_written_bucket(self):
        engine = FaissMemoryEngine(max_record_count=2, load_records=False)
        engine.records = {"success": [], "failure": []}
        with patch.object(engine, "_persist_records"), patch.object(
            engine, "_ensure_faiss", return_value=False
        ):
            for core_pain in ["first", "second", "third"]:
                engine.save_memory(
                    {
                        "product_type": "printer",
                        "strategy": {"core_pain": core_pain},
                        "reward_metrics": {
                            "is_approved": True,
                            "is_grounded": True,
                            "grounded_ctr": 0.05,
                            "predicted_ctr": 0.07,
                        },
                    }
                )

        snapshot = engine.observability_snapshot()
        pains = [item["strategy"]["core_pain"] for item in engine.records["success"]]
        self.assertEqual(pains, ["second", "third"])
        self.assertEqual(snapshot["memory_record_count"]["total"], 2)
        self.assertEqual(snapshot["memory_growth"]["max_record_count"], 2)
        self.assertEqual(snapshot["memory_growth"]["peak_record_count"], 3)
        self.assertEqual(snapshot["memory_growth"]["pruned_count"], 1)
        self.assertTrue(snapshot["memory_growth"]["limit_reached"])

    def test_faiss_fallback_records_count_and_trace(self):
        engine = FaissMemoryEngine(load_records=False)
        engine._set_faiss_fallback("retrieval", RuntimeError("embedding offline"))
        engine._set_faiss_fallback("write", RuntimeError("index offline"))

        snapshot = engine.observability_snapshot()
        self.assertEqual(snapshot["faiss_observability"]["fallback_count"], 2)
        self.assertEqual(
            snapshot["faiss_observability"]["fallback_trace"][0]["operation"],
            "retrieval",
        )
        engine._set_faiss_fallback("retrieval", RuntimeError("embedding offline"))
        snapshot = engine.observability_snapshot()
        retrieval_trace = snapshot["faiss_observability"]["fallback_trace"][0]
        self.assertEqual(retrieval_trace["count"], 2)
        self.assertEqual(snapshot["faiss_observability"]["fallback_count"], 3)
        self.assertEqual(snapshot["backend"], "json_fallback")

    def test_dopamine_telemetry_carries_memory_observability(self):
        state = {
            "env_state": {
                "evidence": {
                    "evidence_quotes": ["The paper jammed halfway."],
                    "trend_signals": ["repair before and after"],
                },
                "raw_reviews": [],
                "trend_signals": [],
            },
            "cognitive_state": {},
            "execution_state": {},
            "telemetry_state": {},
            "world_metrics": {},
            "revision_count": 0,
            "next_nodes": [],
        }
        snapshot = {
            "write_count": 3,
            "skipped_count": 2,
            "retrieval_count": 5,
            "retrieval_hits": {"success": 4, "failure": 1},
            "backend": "json_fallback",
            "faiss_error": "faiss unavailable",
            "memory_record_count": {"success": 8, "failure": 2, "total": 10},
            "memory_growth": {
                "max_record_count": 500,
                "peak_record_count": 10,
                "remaining_capacity": 490,
                "limit_reached": False,
                "limit_reached_count": 0,
                "pruned_count": 0,
            },
            "faiss_observability": {
                "fallback_count": 2,
                "recovery_count": 0,
                "fallback_trace": [{"operation": "retrieval", "error": "faiss unavailable"}],
            },
        }
        with patch(
            "core.workflow.CognitiveAgent.run",
            new=AsyncMock(return_value=("short extraction", NodeMetrics(role_key="dopamine"))),
        ), patch(
            "core.workflow.memory_engine.observability_snapshot", return_value=snapshot
        ):
            result = asyncio.run(parallel_analysis_node(state))

        telemetry = result["telemetry_state"]["analysis_dopamine"]
        self.assertEqual(telemetry["memory_write_count"], 3)
        self.assertEqual(telemetry["memory_skipped_count"], 2)
        self.assertEqual(telemetry["memory_retrieval_hits_success"], 4)
        self.assertEqual(telemetry["memory_record_count_total"], 10)
        self.assertEqual(telemetry["memory_backend"], "json_fallback")
        self.assertEqual(telemetry["memory_faiss_error"], "faiss unavailable")
        self.assertEqual(telemetry["faiss_fallback_count"], 2)
        self.assertEqual(telemetry["memory_remaining_capacity"], 490)

    def test_reporting_aggregates_memory_snapshot_without_summing_counters(self):
        data = {
            "telemetry": {
                "strategy": {
                    "status": "success",
                    "memory_write_count": 3,
                    "memory_retrieval_count": 4,
                    "memory_record_count_total": 10,
                    "memory_backend": "json_fallback",
                    "memory_max_record_count": 500,
                    "memory_peak_record_count": 10,
                    "memory_remaining_capacity": 490,
                    "faiss_fallback_count": 2,
                    "faiss_fallback_trace": [{"operation": "retrieval", "error": "offline"}],
                },
                "cognitive_synthesis": {
                    "status": "success",
                    "memory_write_count": 3,
                    "memory_retrieval_count": 4,
                    "memory_record_count_total": 10,
                    "memory_backend": "json_fallback",
                    "memory_max_record_count": 500,
                    "memory_peak_record_count": 10,
                    "memory_remaining_capacity": 490,
                    "faiss_fallback_count": 2,
                    "faiss_fallback_trace": [{"operation": "write", "error": "newer offline"}],
                },
            }
        }
        aggregate = telemetry_node_aggregate(telemetry_rows("printer", data))

        self.assertTrue(all(row["max_memory_write_count"] == 3 for row in aggregate))
        self.assertTrue(all(row["max_memory_record_count_total"] == 10 for row in aggregate))
        self.assertTrue(all(row["max_memory_record_limit"] == 500 for row in aggregate))
        self.assertTrue(all(row["max_faiss_fallback_count"] == 2 for row in aggregate))
        synthesis_row = next(row for row in aggregate if row["node"] == "cognitive_synthesis")
        self.assertIn("newer offline", synthesis_row["faiss_fallback_traces"])

    def test_analytics_memory_telemetry_is_captured_after_write(self):
        state = {
            "env_state": {"product_category": "printer"},
            "cognitive_state": {"profile": {"painpoint": {}}, "strategy": {}},
            "execution_state": {"storyboard": {}},
            "telemetry_state": {},
            "world_metrics": {"is_approved": False, "is_grounded": False},
            "revision_count": 0,
            "next_nodes": [],
        }
        with patch("core.workflow.memory_engine.save_memory"), patch(
            "core.workflow.memory_engine.observability_snapshot",
            return_value={
                "write_count": 7,
                "skipped_count": 1,
                "retrieval_count": 4,
                "retrieval_hits": {"success": 2, "failure": 1},
                "backend": "json_fallback",
                "faiss_error": "",
                "memory_record_count": {"success": 5, "failure": 3, "total": 8},
                "memory_growth": {
                    "max_record_count": 500,
                    "peak_record_count": 8,
                    "remaining_capacity": 492,
                    "limit_reached": False,
                    "limit_reached_count": 0,
                    "pruned_count": 0,
                },
                "faiss_observability": {
                    "fallback_count": 4,
                    "recovery_count": 0,
                    "fallback_trace": [{"operation": "write", "error": "faiss unavailable"}],
                },
            },
        ):
            result = asyncio.run(analytics_node(state))

        telemetry = result["telemetry_state"]["analytics_memory"]
        self.assertEqual(telemetry["memory_write_count"], 7)
        self.assertEqual(telemetry["memory_record_count_total"], 8)
        self.assertEqual(telemetry["memory_remaining_capacity"], 492)
        self.assertEqual(telemetry["faiss_fallback_count"], 4)
        self.assertEqual(telemetry["role_key"], "analytics_memory")


if __name__ == "__main__":
    unittest.main()
