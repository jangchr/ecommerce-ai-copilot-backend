import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_amazon_shadow_eval as runner


class AmazonShadowEvalRunnerTest(unittest.TestCase):
    def test_row_from_response_extracts_shadow_fields(self):
        item = {"category": "balsamic_vinegar", "url": "https://www.amazon.com/dp/B00QIIMCCW"}
        payload = {
            "shadow_sources": {
                "mode": "amazon_shadow",
                "amazon_review_api": {
                    "status": "success",
                    "source_confidence": 0.82,
                    "latency_ms": 1234.5,
                    "evidence_preview": ["Cap cracked during shipping."],
                    "metadata": {
                        "product_title": "Balsamic Vinegar",
                        "rating": "4.6",
                        "review_count": "485",
                        "category_hint": "Grocery",
                        "bullet_points": ["Aged flavor", "Glass bottle"],
                    },
                    "error": "",
                },
                "memory_write_allowed": False,
                "used_for_generation": False,
            }
        }

        row = runner.row_from_response(item, payload)

        self.assertEqual(row["provider_status"], "success")
        self.assertEqual(row["source_confidence"], 0.82)
        self.assertTrue(row["product_title_present"])
        self.assertTrue(row["rating_present"])
        self.assertTrue(row["review_count_present"])
        self.assertEqual(row["evidence_preview_count"], 1)
        self.assertEqual(row["bullet_points_count"], 2)
        self.assertTrue(row["category_hint_present"])
        self.assertFalse(row["fallback_required"])
        self.assertFalse(row["memory_write_allowed"])
        self.assertFalse(row["used_for_generation"])

    def test_safety_check_marks_invalid_shadow_flags(self):
        item = {"category": "printer", "url": "https://example.test"}
        payload = {
            "shadow_sources": {
                "amazon_review_api": {"status": "success", "source_confidence": 0.9},
                "memory_write_allowed": True,
                "used_for_generation": True,
            }
        }

        row = runner.row_from_response(item, payload)

        self.assertEqual(row["error_type"], "safety_fail")
        self.assertIn("memory_write_allowed", row["notes"])
        self.assertIn("used_for_generation", row["notes"])

    def test_run_evaluation_writes_csv_and_markdown_without_real_http(self):
        items = [{"category": "phone_case", "url": "https://www.amazon.com/dp/B0D6X6GZ8Y"}]
        payload = {
            "shadow_sources": {
                "amazon_review_api": {
                    "status": "unavailable",
                    "source_confidence": 0.0,
                    "latency_ms": 50.0,
                    "evidence_preview": [],
                    "metadata": {},
                    "error": "blocked",
                },
                "memory_write_allowed": False,
                "used_for_generation": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "post_debug_copilot",
            return_value=payload,
        ) as post:
            output_dir = runner.run_evaluation(
                items=items,
                base_url="http://127.0.0.1:8001",
                output_root=Path(tmpdir),
            )

            post.assert_called_once()
            csv_path = output_dir / "amazon_shadow_eval_summary.csv"
            report_path = output_dir / "amazon_shadow_eval_report.md"
            self.assertTrue(csv_path.exists())
            self.assertTrue(report_path.exists())

            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["provider_status"], "unavailable")
            self.assertEqual(rows[0]["memory_write_allowed"], "False")
            self.assertEqual(rows[0]["used_for_generation"], "False")

            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Total URLs: 1", report)
            self.assertIn("Unavailable count: 1", report)
            self.assertIn("Product API called: false", report)
            self.assertIn("Debug Copilot called: true", report)
            self.assertIn("The runner never calls `/api/v1/generate-copilot`", report)

    def test_probe_only_uses_debug_source_probe_and_skips_debug_copilot(self):
        items = [{"category": "phone_case", "url": "https://www.amazon.com/dp/B0D6X6GZ8Y"}]
        payload = {
            "fallback_required": False,
            "memory_write_allowed": False,
            "results": [
                {
                    "provider": "amazon_review_api",
                    "status": "success",
                    "source_confidence": 0.88,
                    "latency_ms": 42.0,
                    "evidence_preview": ["The case yellowed after a month."],
                    "metadata": {
                        "product_title": "Phone Case",
                        "rating": "4.3",
                        "review_count": "991",
                        "category_hint": "Cell Phones",
                        "bullet_points": ["Clear case"],
                    },
                    "error": "",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            runner,
            "post_debug_source_probe",
            return_value=payload,
        ) as probe, patch.object(
            runner,
            "post_debug_copilot",
            side_effect=AssertionError("probe-only must not call debug-copilot"),
        ):
            output_dir = runner.run_evaluation(
                items=items,
                base_url="http://127.0.0.1:8001",
                output_root=Path(tmpdir),
                probe_only=True,
            )

            probe.assert_called_once()
            csv_path = output_dir / "amazon_shadow_eval_summary.csv"
            report_path = output_dir / "amazon_shadow_eval_report.md"
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["provider_status"], "success")
            self.assertEqual(rows[0]["memory_write_allowed"], "False")
            self.assertEqual(rows[0]["used_for_generation"], "False")

            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Product API called: false", report)
            self.assertIn("Debug Copilot called: false", report)
            self.assertIn("Probe-only mode: true", report)


if __name__ == "__main__":
    unittest.main()
