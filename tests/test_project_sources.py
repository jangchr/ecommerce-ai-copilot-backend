import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agent_runs import build_lightweight_artifact_registry
from main import _graph_report_markdown, app
from source_adapters.project_sources import (
    SAFETY_BOUNDARIES,
    build_project_source,
    build_source_quality_gate,
    detect_source_type_from_url,
    parse_amazon_asin,
    parse_shopify_handle,
)
from tests.test_pasted_reviews_endpoint import GENERATED_REVIEWS_BRIEF


class ProjectSourceAdapterTests(unittest.TestCase):
    def test_amazon_url_detection_and_asin_paths(self):
        for url in [
            "https://www.amazon.com/example/dp/B0TEST1234?tag=tracking",
            "https://smile.amazon.com/gp/product/B0TEST1234/ref=something",
        ]:
            with self.subTest(url=url):
                self.assertEqual(detect_source_type_from_url(url), "amazon_url")
                self.assertEqual(parse_amazon_asin(url), "B0TEST1234")

    def test_amazon_failure_is_safe_manual_fallback(self):
        failed_fetch = {
            "succeeded": False,
            "status_code": 503,
            "content_type": "",
            "body": "",
            "final_url": "https://www.amazon.com/dp/B0TEST1234",
            "error_type": "http_error",
            "error": "HTTP 503",
        }
        with patch(
            "source_adapters.project_sources.fetch_public_source_url",
            return_value=failed_fetch,
        ):
            bundle = build_project_source(
                {
                    "project_id": "source_test_project",
                    "source_type": "amazon_url",
                    "source_url": "https://www.amazon.com/dp/B0TEST1234",
                    "product_name": "Test product",
                }
            )

        source = bundle["project_source"]
        self.assertIn(source["source_status"], {"partial", "fallback_required"})
        self.assertIn("manual_reviews_recommended", source["warnings"])
        self.assertIn("no_verified_purchase_classification", source["warnings"])
        self.assertTrue(source["source_summary"]["manual_fallback_needed"])
        self.assertFalse(source["safety_boundaries"]["anti_bot_bypass_used"])
        self.assertFalse(bundle["adapter_result"]["anti_bot_bypass_used"])
        self.assertEqual(bundle["source_quality_gate"]["status"], "fallback_required")

    def test_shopify_public_json_extracts_safe_product_fields(self):
        self.assertEqual(
            detect_source_type_from_url("https://example-shop.com/products/test-handle"),
            "shopify_url",
        )
        self.assertEqual(
            parse_shopify_handle("https://example-shop.com/products/test-handle"),
            "test-handle",
        )
        fetch = {
            "succeeded": True,
            "status_code": 200,
            "content_type": "application/json",
            "body": (
                '{"title":"Travel Blender","description":"Compact blender.",'
                '"vendor":"Demo Brand","type":"Kitchen Appliance",'
                '"handle":"test-handle","variants":[{"id":1},{"id":2}],'
                '"images":[{"src":"https://cdn.example.com/blender.jpg"}]}'
            ),
            "final_url": "https://example-shop.com/products/test-handle.js",
            "error_type": "",
            "error": "",
        }
        with patch(
            "source_adapters.project_sources.fetch_public_source_url",
            return_value=fetch,
        ):
            bundle = build_project_source(
                {
                    "source_type": "shopify_url",
                    "source_url": "https://example-shop.com/products/test-handle",
                }
            )

        source = bundle["project_source"]
        artifact = bundle["source_evidence_artifact"]
        self.assertEqual(source["product_name"], "Travel Blender")
        self.assertEqual(source["product_category"], "Kitchen Appliance")
        self.assertEqual(artifact["shopify_handle"], "test-handle")
        self.assertIn("manual_reviews_recommended", source["warnings"])

    def test_manual_csv_source_dedupes_and_classifies_reviews(self):
        bundle = build_project_source(
            {
                "project_id": "csv_project",
                "source_type": "csv_reviews",
                "product_name": "Travel Blender",
                "csv_text": (
                    "review,rating,verified,variant\n"
                    "Hard to clean after one smoothie,2,true,Blue\n"
                    "Hard to clean after one smoothie,2,true,Blue\n"
                    "Love it for travel,5,false,\n"
                    "Too expensive for one cup,2,false,\n"
                ),
            },
            network_fetch=False,
        )
        source = bundle["project_source"]
        artifact = bundle["source_evidence_artifact"]
        categories = {
            category
            for item in artifact["review_classifications"]
            for category in item["categories"]
        }
        self.assertEqual(source["source_summary"]["review_count"], 4)
        self.assertEqual(source["source_summary"]["unique_review_count"], 3)
        self.assertEqual(source["source_summary"]["duplicate_review_count"], 1)
        self.assertIn("pain_point", categories)
        self.assertIn("positive_signal", categories)
        self.assertIn("buyer_objection", categories)
        self.assertTrue(any(item["verified_purchase"] for item in artifact["review_classifications"]))
        self.assertEqual(bundle["source_quality_gate"]["status"], "warning")
        self.assertTrue(bundle["source_quality_gate"]["allows_agent_run"])

    def test_unsupported_source_gate_is_blocked(self):
        gate = build_source_quality_gate(
            {
                "source_type": "unsupported",
                "source_confidence": 0.0,
                "warnings": [],
            },
            {"evidence_quotes": [], "product_signals": [], "warnings": []},
        )
        self.assertEqual(gate["status"], "blocked")
        self.assertFalse(gate["allows_agent_run"])
        self.assertEqual(gate["safety_boundaries"], SAFETY_BOUNDARIES)


class ProjectSourceEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {"AGENT_GRAPH_STORAGE_PATH": self.tempdir.name},
        )
        self.env.start()
        self.client = TestClient(app)
        created = self.client.post(
            "/api/v1/projects",
            json={
                "project_name": "Source Intelligence Test",
                "product_name": "Travel Blender",
                "source_type": "manual",
            },
        )
        self.project_id = created.json()["project"]["project_id"]

    def tearDown(self):
        self.env.stop()
        self.tempdir.cleanup()

    def _create_manual_source(self):
        return self.client.post(
            f"/api/v1/projects/{self.project_id}/sources",
            json={
                "source_type": "pasted_reviews",
                "product_name": "Travel Blender",
                "product_category": "kitchen_appliance",
                "product_description": "A compact rechargeable blender.",
                "pasted_reviews": (
                    "Hard to clean after one smoothie.\n"
                    "Too loud for early mornings.\n"
                    "Love it for travel and work."
                ),
                "source_notes": "Visible customer feedback sample.",
            },
        )

    def test_source_crud_history_summary_and_registry_lineage(self):
        response = self._create_manual_source()
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        source = payload["project_source"]
        artifact = payload["source_evidence_artifact"]
        gate = payload["source_quality_gate"]
        snapshot = payload["source_snapshot"]
        registry = payload["artifact_registry"]
        source_id = source["source_id"]

        self.assertEqual(source["source_version"], "project_source_v1")
        self.assertEqual(source["project_id"], self.project_id)
        self.assertEqual(artifact["artifact_version"], "source_evidence_artifact_v1")
        self.assertEqual(gate["gate_version"], "source_quality_gate_v1")
        self.assertEqual(snapshot["snapshot_version"], "source_snapshot_v1")
        self.assertTrue(gate["allows_agent_run"])
        artifact_types = {item["artifact_type"] for item in registry["artifacts"]}
        self.assertTrue(
            {
                "project_source",
                "source_quality_gate",
                "source_evidence_artifact",
                "source_snapshot",
            }.issubset(artifact_types)
        )
        self.assertTrue(registry["lineage_summary"]["has_source_artifacts"])
        self.assertTrue(registry["lineage_summary"]["has_source_quality_gate"])
        self.assertTrue(registry["lineage_summary"]["has_review_classifications"])
        self.assertFalse(registry["lineage_summary"]["is_linear_workflow"])

        source_read = self.client.get(
            f"/api/v1/projects/{self.project_id}/sources/{source_id}"
        )
        evidence_read = self.client.get(
            f"/api/v1/projects/{self.project_id}/sources/{source_id}/evidence"
        )
        sources = self.client.get(f"/api/v1/projects/{self.project_id}/sources")
        history_sources = self.client.get(
            f"/api/v1/projects/{self.project_id}/history/sources"
        )
        history_artifacts = self.client.get(
            f"/api/v1/projects/{self.project_id}/history/source-artifacts"
        )
        history_gates = self.client.get(
            f"/api/v1/projects/{self.project_id}/history/source-quality-gates"
        )
        history_snapshots = self.client.get(
            f"/api/v1/projects/{self.project_id}/history/source-snapshots"
        )
        graph_summary = self.client.get(
            f"/api/v1/projects/{self.project_id}/graph-summary"
        ).json()

        self.assertEqual(source_read.json()["project_source"]["source_id"], source_id)
        self.assertEqual(
            evidence_read.json()["source_evidence_artifact"]["source_id"],
            source_id,
        )
        self.assertEqual(sources.json()["sources"][0]["source_id"], source_id)
        self.assertTrue(history_sources.json()["sources"])
        self.assertTrue(history_artifacts.json()["source_artifacts"])
        self.assertTrue(history_gates.json()["source_quality_gates"])
        self.assertTrue(history_snapshots.json()["source_snapshots"])
        summary = graph_summary["project"]["graph_summary"]
        self.assertEqual(summary["source_count"], 1)
        self.assertEqual(summary["source_artifact_count"], 1)
        self.assertEqual(summary["source_quality_gate_count"], 1)
        self.assertEqual(summary["source_snapshot_count"], 1)
        self.assertEqual(summary["latest_source_id"], source_id)
        self.assertIn("recent_sources", graph_summary)
        self.assertIn("recent_source_artifacts", graph_summary)

    def test_preview_does_not_persist_and_source_generate_reuses_existing_flow(self):
        preview = self.client.post(
            f"/api/v1/projects/{self.project_id}/sources/preview",
            json={
                "source_type": "text_review_batch",
                "product_name": "Travel Blender",
                "pasted_reviews": "Hard to clean.\nGreat for travel.\nToo loud in the morning.",
            },
        )
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertTrue(preview.json()["preview"])
        self.assertEqual(
            self.client.get(
                f"/api/v1/projects/{self.project_id}/sources"
            ).json()["source_count"],
            0,
        )

        created = self._create_manual_source().json()
        source_id = created["project_source"]["source_id"]
        with patch(
            "main.generate_pasted_reviews_brief",
            new=AsyncMock(return_value=GENERATED_REVIEWS_BRIEF),
        ):
            generated = self.client.post(
                f"/api/v1/projects/{self.project_id}/sources/{source_id}/generate",
                json={
                    "target_platform": "TikTok",
                    "goal": "tiktok_ctr",
                    "output_language": "en",
                },
            )
        self.assertEqual(generated.status_code, 200, generated.text)
        data = generated.json()["data"]
        self.assertEqual(data["project_id"], self.project_id)
        self.assertEqual(data["project_source"]["source_id"], source_id)
        self.assertEqual(
            data["source_evidence_artifact"]["artifact_version"],
            "source_evidence_artifact_v1",
        )
        self.assertEqual(
            data["source_quality_gate"]["gate_version"],
            "source_quality_gate_v1",
        )
        self.assertEqual(data["llm_evidence_packet"]["packet_version"], "source_evidence_v1")
        self.assertFalse(
            data["source_evidence_artifact"]["safety_boundaries"][
                "anti_bot_bypass_used"
            ]
        )

    def test_product_only_public_source_requires_manual_reviews(self):
        failed_fetch = {
            "succeeded": False,
            "status_code": 503,
            "content_type": "",
            "body": "",
            "final_url": "https://www.amazon.com/dp/B0TEST1234",
            "error_type": "http_error",
            "error": "HTTP 503",
        }
        with patch(
            "source_adapters.project_sources.fetch_public_source_url",
            return_value=failed_fetch,
        ):
            created = self.client.post(
                f"/api/v1/projects/{self.project_id}/sources",
                json={
                    "source_type": "amazon_url",
                    "source_url": "https://www.amazon.com/dp/B0TEST1234",
                    "product_name": "Test Product",
                },
            )
        source_id = created.json()["project_source"]["source_id"]
        generated = self.client.post(
            f"/api/v1/projects/{self.project_id}/sources/{source_id}/generate",
            json={},
        )
        self.assertEqual(generated.status_code, 409)
        self.assertEqual(generated.json()["status"], "fallback_required")
        self.assertEqual(generated.json()["error_type"], "manual_reviews_required")

    def test_source_report_sections_and_safety_boundary(self):
        bundle = self._create_manual_source().json()
        markdown = _graph_report_markdown(
            {
                "report_title": "Source Report",
                "report_version": "agent_graph_report_v2",
                "project_id": self.project_id,
                "project": {"project_name": "Source Test"},
                "summary": {},
                "graph_state_snapshot": {},
                "artifact_registry": bundle["artifact_registry"],
                "project_source": bundle["project_source"],
                "source_quality_gate": bundle["source_quality_gate"],
                "source_evidence_artifact": bundle["source_evidence_artifact"],
                "source_snapshot": bundle["source_snapshot"],
                "safety_boundaries": {
                    "external_api_called": False,
                    "cost_incurred_by_crossgrowth": False,
                    "llm_autonomous_decision_enabled": False,
                    "anti_bot_bypass_used": False,
                },
            }
        )
        self.assertIn("## Project Source", markdown)
        self.assertIn("## Source Quality Gate", markdown)
        self.assertIn("## Source Evidence", markdown)
        self.assertIn("## Review Classification", markdown)
        self.assertIn("## Safety Boundaries", markdown)
        self.assertIn("anti_bot_bypass_used: false", markdown)


class SourceArtifactRegistryTests(unittest.TestCase):
    def test_registry_links_source_chain_to_generation_packets(self):
        source = {
            "source_version": "project_source_v1",
            "source_id": "source_1",
            "source_type": "amazon_url",
            "source_summary": {"manual_fallback_needed": False},
        }
        artifact = {
            "artifact_version": "source_evidence_artifact_v1",
            "artifact_id": "source_artifact_1",
            "source_id": "source_1",
            "source_type": "amazon_url",
            "review_classifications": [{"categories": ["positive_signal"]}],
        }
        registry = build_lightweight_artifact_registry(
            generation_data={
                "project_source": source,
                "source_quality_gate": {
                    "gate_version": "source_quality_gate_v1",
                    "status": "passed",
                },
                "source_evidence_artifact": artifact,
                "source_snapshot": {
                    "snapshot_version": "source_snapshot_v1",
                    "source_id": "source_1",
                },
                "llm_evidence_packet": {"packet_version": "source_evidence_v1"},
                "video_generation_packet": {"packet_version": "video_generation_v1"},
            }
        )
        by_type = {
            item["artifact_type"]: item
            for item in registry["artifacts"]
        }
        self.assertIn("amazon_source", by_type)
        self.assertIn(
            by_type["project_source"]["artifact_id"],
            by_type["source_quality_gate"]["parent_artifact_ids"],
        )
        self.assertIn(
            by_type["source_quality_gate"]["artifact_id"],
            by_type["source_evidence_artifact"]["parent_artifact_ids"],
        )
        self.assertIn(
            by_type["source_evidence_artifact"]["artifact_id"],
            by_type["llm_evidence_packet"]["parent_artifact_ids"],
        )
        self.assertTrue(registry["lineage_summary"]["has_source_artifacts"])
        self.assertTrue(registry["lineage_summary"]["has_review_classifications"])


if __name__ == "__main__":
    unittest.main()

