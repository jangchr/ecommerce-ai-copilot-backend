import unittest

from fastapi.testclient import TestClient

from main import AGENT_RUN_STORE, VIDEO_JOB_STORE, app


VIDEO_PACKET = {
    "packet_version": "video_generation_v1",
    "intended_use": "video_prompt_export",
    "video": {
        "platform": "TikTok",
        "recommended_duration_seconds": 20,
        "aspect_ratio": "9:16",
    },
    "scenes": [
        {
            "scene_id": 1,
            "duration_seconds": 5,
            "visual_prompt": "Show a compact blender on a kitchen counter.",
            "narration": "One smoothie should not make cleanup hard.",
            "overlay_text": "Hard to clean?",
            "evidence_quote": "Hard to clean after one smoothie",
        },
        {
            "scene_id": 2,
            "duration_seconds": 5,
            "visual_prompt": "Show someone blending early in the morning.",
            "narration": "Nobody wants to wake the whole house.",
            "overlay_text": "Too loud?",
            "evidence_quote": "Too loud for early mornings",
        },
    ],
    "full_video_prompt": "Create a 9:16 TikTok video about a compact blender.",
    "evidence_boundary": "Use only supplied review evidence and keep claims conservative.",
    "export_formats": {
        "generic_video_prompt": "Create a 9:16 TikTok video about a compact blender.",
        "capcut_shot_list": "Scene 1 - 5s - Show compact blender.\\nScene 2 - 5s - Blend early morning.",
        "runway_style_prompt": "Cinematic close-up of compact blender in a bright kitchen.",
        "pika_style_prompt": "Short motion video, compact blender, quick cuts.",
    },
}


class VideoGenerationJobEndpointTest(unittest.TestCase):
    def setUp(self):
        AGENT_RUN_STORE.clear()
        VIDEO_JOB_STORE.clear()
        self.client = TestClient(app)

    def _create_video_generation_job(self, provider: str = "runway") -> str:
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": provider,
                "output_language": "en",
            },
        )
        self.assertEqual(created.status_code, 200)
        return created.json()["job"]["job_id"]

    def _record_external_experiment(self, job_id: str, **overrides):
        payload = {
            "tool_name": "gemini",
            "prompt_type": "gemini_video_prompt",
            "result_url": "https://example.com/gemini-video.mp4",
            "actual_cost_usd": 0.25,
            "product_consistency_score": 5,
            "storyboard_following_score": 5,
            "visual_quality_score": 5,
            "ad_readiness_score": 5,
            "overall_score": 5,
            "notes": "Recorded external result.",
        }
        payload.update(overrides)
        return self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/experiments",
            json=payload,
        )

    def test_video_generation_providers_endpoint_lists_supported_providers(self):
        response = self.client.get(
            "/api/v1/video-generation/providers",
            headers={"X-Request-ID": "video-providers-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-providers-1")

        providers = {item["provider"]: item for item in payload["providers"]}
        for provider in ["manual_export", "generic", "capcut", "runway", "pika"]:
            self.assertIn(provider, providers)
            self.assertIn("export_key", providers[provider])
            self.assertFalse(providers[provider]["external_api_ready"])
            self.assertIn("supports_async_polling", providers[provider])
            self.assertIn("requires_api_key", providers[provider])
            self.assertIn("env_key_name", providers[provider])
            self.assertIn("create_mode", providers[provider])
            self.assertIn("status_lifecycle", providers[provider])
            self.assertIn("recommended_use", providers[provider])

        self.assertFalse(providers["manual_export"]["requires_api_key"])
        self.assertFalse(providers["manual_export"]["supports_async_polling"])
        self.assertTrue(providers["runway"]["requires_api_key"])
        self.assertTrue(providers["runway"]["supports_async_polling"])
        self.assertEqual(providers["runway"]["env_key_name"], "RUNWAY_API_KEY")
        self.assertFalse(providers["runway"]["external_api_ready"])
        self.assertTrue(providers["pika"]["requires_api_key"])
        self.assertEqual(providers["pika"]["env_key_name"], "PIKA_API_KEY")

    def test_video_generation_provider_plan_endpoint_returns_runway_plan(self):
        response = self.client.get(
            "/api/v1/video-generation/providers/runway/plan",
            headers={"X-Request-ID": "video-provider-plan-runway-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["provider"], "runway")
        self.assertEqual(payload["request_id"], "video-provider-plan-runway-1")
        plan = payload["plan"]
        self.assertFalse(plan["external_api_ready"])
        self.assertTrue(plan["requires_api_key"])
        self.assertEqual(plan["env_key_name"], "RUNWAY_API_KEY")
        self.assertEqual(plan["create_mode"], "planned_external_api")
        self.assertTrue(plan["supports_async_polling"])
        self.assertIn("queued", plan["supported_statuses"])
        self.assertIn("processing", plan["supported_statuses"])
        self.assertEqual(plan["selected_export_key"], "runway_style_prompt")
        self.assertEqual(plan["export_key"], "runway_style_prompt")
        self.assertIn("visual video generation", plan["recommended_use"])
        self.assertIn("disabled", " ".join(plan["provider_limitations"]).lower())
        self.assertTrue(plan["warnings"])
        self.assertIn("disabled", " ".join(plan["warnings"]).lower())

    def test_video_generation_provider_plan_endpoint_returns_manual_plan(self):
        response = self.client.get("/api/v1/video-generation/providers/manual_export/plan")

        self.assertEqual(response.status_code, 200)
        plan = response.json()["plan"]
        self.assertEqual(plan["provider"], "manual_export")
        self.assertFalse(plan["requires_api_key"])
        self.assertFalse(plan["supports_async_polling"])
        self.assertEqual(plan["create_mode"], "manual_export")
        self.assertEqual(plan["selected_export_key"], "generic_video_prompt")
        self.assertIn("preferred video workflow", plan["recommended_use"])
        self.assertIn("No external API", " ".join(plan["warnings"]))
        self.assertIn("manual_export_completed", plan["supported_statuses"])

    def test_video_generation_provider_plan_endpoint_returns_404_for_unknown_provider(self):
        response = self.client.get(
            "/api/v1/video-generation/providers/unknown_provider/plan",
            headers={"X-Request-ID": "video-provider-plan-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-provider-plan-missing-1")

    def test_create_video_generation_job_selects_provider_export_prompt(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
                "output_language": "en",
            },
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["provider"], "runway")
        self.assertEqual(job["provider_payload"]["selected_export_key"], "runway_style_prompt")
        self.assertEqual(job["provider_payload"]["prompt"], VIDEO_PACKET["export_formats"]["runway_style_prompt"])
        self.assertEqual(job["provider_payload"]["next_action"], "manual_copy_to_video_tool")
        self.assertEqual(job["provider_payload"]["create_mode"], "planned_external_api")
        self.assertFalse(job["provider_payload"]["external_api_ready"])
        self.assertTrue(job["provider_payload"]["requires_api_key"])
        self.assertEqual(job["provider_payload"]["env_key_name"], "RUNWAY_API_KEY")
        self.assertTrue(job["provider_payload"]["supports_async_polling"])
        self.assertIn("queued", job["provider_payload"]["status_lifecycle"])
        self.assertEqual(job["provider_payload"]["prompt_title"], "Runway-style visual prompt")
        self.assertIn("visual video generation", job["provider_payload"]["recommended_use"])
        self.assertIn("Runway API integration is planned but disabled", " ".join(job["provider_payload"]["provider_limitations"]))
        self.assertEqual(job["provider_payload"]["scene_count"], 2)
        self.assertEqual(job["provider_payload"]["recommended_duration_seconds"], 20)
        self.assertEqual(job["provider_payload"]["aspect_ratio"], "9:16")
        self.assertEqual(job["provider_payload"]["evidence_boundary"], VIDEO_PACKET["evidence_boundary"])
        cost_estimate = job["provider_payload"]["cost_estimate"]
        self.assertEqual(cost_estimate["provider"], "runway")
        self.assertEqual(cost_estimate["model"], "runway_gen4_turbo")
        self.assertTrue(cost_estimate["pricing_is_estimate"])
        self.assertGreater(cost_estimate["estimated_cost_usd"], 0)
        self.assertTrue(cost_estimate["requires_user_confirmation"])
        self.assertFalse(cost_estimate["external_api_call_planned"])

    def test_create_video_generation_job_accepts_export_key_alias(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "capcut_shot_list",
                "output_language": "en",
            },
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["provider"], "capcut")
        self.assertEqual(job["provider_payload"]["selected_export_key"], "capcut_shot_list")
        self.assertEqual(job["provider_payload"]["prompt"], VIDEO_PACKET["export_formats"]["capcut_shot_list"])
        self.assertEqual(job["provider_payload"]["prompt_title"], "CapCut shot list")
        self.assertIn("editing shot list", job["provider_payload"]["recommended_use"])

    def test_create_video_generation_job_rejects_unsupported_provider(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "unknown_video_tool",
            },
            headers={"X-Request-ID": "video-job-provider-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-provider-invalid-1")
        self.assertIn("unsupported", payload["error"])
        self.assertIn("runway", payload["supported_providers"])

    def test_create_video_generation_job_returns_manual_export_payload(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
                "output_language": "en",
            },
            headers={"X-Request-ID": "video-job-create-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-create-1")

        job = payload["job"]
        self.assertTrue(job["job_id"].startswith("video_job_"))
        self.assertEqual(job["status"], "ready_for_manual_export")
        self.assertEqual(job["provider"], "manual_export")
        self.assertEqual(job["video_generation_packet"]["packet_version"], "video_generation_v1")
        self.assertEqual(job["provider_payload"]["handoff_type"], "manual_export")
        self.assertEqual(job["provider_payload"]["prompt_title"], "Manual video export prompt")
        self.assertIn("preferred video workflow", job["provider_payload"]["recommended_use"])
        self.assertIn("No external video API is called", " ".join(job["provider_payload"]["provider_limitations"]))
        self.assertIn("generic_video_prompt", job["provider_payload"]["export_formats"])
        self.assertIn("capcut_shot_list", job["provider_payload"]["export_formats"])
        self.assertEqual(len(job["provider_payload"]["scenes"]), 2)
        cost_estimate = job["provider_payload"]["cost_estimate"]
        self.assertEqual(cost_estimate["provider"], "manual_export")
        self.assertEqual(cost_estimate["estimated_cost_usd"], 0)
        self.assertEqual(cost_estimate["cost_level"], "free")
        self.assertFalse(cost_estimate["requires_user_confirmation"])
        self.assertFalse(cost_estimate["external_api_call_planned"])
        self.assertEqual(job["result"]["result_url"], "")
        self.assertEqual(job["history"][0]["event"], "created")
        self.assertEqual(job["history"][0]["status"], "ready_for_manual_export")

    def test_update_video_generation_job_result_records_external_result(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
                "output_language": "en",
            },
        ).json()

        job_id = created["job"]["job_id"]
        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/result",
            json={
                "status": "external_result_ready",
                "result_url": "https://example.com/video.mp4",
                "preview_url": "https://example.com/preview.jpg",
                "download_url": "https://example.com/download.mp4",
                "provider_job_id": "runway_job_123",
                "notes": "Generated externally from copied prompt.",
            },
            headers={"X-Request-ID": "video-job-result-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-result-1")

        job = payload["job"]
        self.assertEqual(job["job_id"], job_id)
        self.assertEqual(job["status"], "external_result_ready")
        self.assertEqual(job["result"]["result_url"], "https://example.com/video.mp4")
        self.assertEqual(job["result"]["preview_url"], "https://example.com/preview.jpg")
        self.assertEqual(job["result"]["download_url"], "https://example.com/download.mp4")
        self.assertEqual(job["result"]["provider_job_id"], "runway_job_123")
        self.assertTrue(job["history"])
        self.assertIn("status_changed", [event["event"] for event in job["history"]])
        self.assertEqual(job["history"][-1]["event"], "result_update")
        self.assertEqual(job["history"][-1]["status"], "external_result_ready")

    def test_update_video_generation_job_result_falls_back_to_manual_completed_status(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
            },
        ).json()

        job_id = created["job"]["job_id"]
        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/result",
            json={
                "status": "not_supported",
                "notes": "Copied into a manual editor.",
            },
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(job["status"], "manual_export_completed")
        self.assertEqual(job["result"]["notes"], "Copied into a manual editor.")
        self.assertEqual(job["history"][-1]["event"], "result_update")

    def test_update_video_generation_job_result_rejects_invalid_transition(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
            },
        ).json()
        job_id = created["job"]["job_id"]

        first = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/result",
            json={
                "status": "external_result_ready",
                "result_url": "https://example.com/video.mp4",
            },
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/result",
            json={
                "status": "manual_export_completed",
                "notes": "Should not move backward.",
            },
            headers={"X-Request-ID": "video-job-invalid-transition-1"},
        )

        self.assertEqual(second.status_code, 400)
        payload = second.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-invalid-transition-1")
        self.assertIn("invalid video job status transition", payload["error"])

    def test_update_video_generation_job_result_returns_404_for_missing_job(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/video_job_missing/result",
            json={
                "status": "external_result_ready",
                "result_url": "https://example.com/video.mp4",
            },
            headers={"X-Request-ID": "video-job-result-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-result-missing-1")

    def test_record_external_video_experiment_appends_manual_tracking_record(self):
        job_id = self._create_video_generation_job()

        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/experiments",
            json={
                "tool_name": "gemini",
                "prompt_type": "gemini_video_prompt",
                "result_url": "https://example.com/gemini-video.mp4",
                "preview_url": "https://example.com/gemini-preview.jpg",
                "actual_cost_usd": 0.25,
                "product_consistency_score": 5,
                "storyboard_following_score": 4,
                "visual_quality_score": 4,
                "ad_readiness_score": 3,
                "overall_score": 4,
                "notes": "Good product consistency.",
                "failure_reason": "",
            },
            headers={"X-Request-ID": "video-experiment-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-experiment-1")
        job = payload["job"]
        self.assertEqual(job["status"], "ready_for_manual_export")
        experiments = job["external_video_experiments"]
        self.assertEqual(len(experiments), 1)
        self.assertEqual(job["external_experiments"][0]["result_url"], "https://example.com/gemini-video.mp4")
        experiment = experiments[0]
        self.assertTrue(experiment["experiment_id"].startswith("video_experiment_"))
        self.assertEqual(experiment["tool_name"], "gemini")
        self.assertEqual(experiment["prompt_type"], "gemini_video_prompt")
        self.assertEqual(experiment["result_url"], "https://example.com/gemini-video.mp4")
        self.assertFalse(experiment["external_api_called"])
        self.assertFalse(experiment["cost_incurred_by_crossgrowth"])
        self.assertEqual(experiment["overall_score"], 4)
        decision = experiment["agent_feedback_decision"]
        self.assertFalse(decision["has_feedback"])
        self.assertEqual(decision["decision_type"], "feedback_recorded_no_rework")
        self.assertEqual(decision["source_agent_id"], "experiment_agent")
        self.assertEqual(decision["issue_type"], "none")
        self.assertEqual(job["latest_agent_feedback_decision"]["decision_type"], "feedback_recorded_no_rework")
        self.assertFalse(job["latest_agent_feedback_decision"]["has_feedback"])
        self.assertEqual(job["agent_graph_feedback"]["feedback_version"], "experiment_feedback_loop_v1")
        self.assertEqual(job["agent_graph_feedback"]["decisions"][0]["issue_type"], "none")
        self.assertNotIn("latest_experiment_rework_run_id", job)
        self.assertNotIn("latest_rework_artifact_type", job)
        self.assertNotIn("triggered_rework_run_id", job["external_video_experiments"][0]["agent_feedback_decision"])
        history_events = [event["event"] for event in job["history"]]
        self.assertIn("external_video_experiment_recorded", history_events)
        self.assertIn("experiment_feedback_recorded", history_events)

        fetched = self.client.get(f"/api/v1/video-generation/jobs/{job_id}")
        self.assertEqual(fetched.status_code, 200)
        fetched_job = fetched.json()["job"]
        self.assertEqual(fetched_job["external_video_experiments"][0]["experiment_id"], experiment["experiment_id"])

        listed = self.client.get("/api/v1/video-generation/jobs?limit=10")
        selected = next(item for item in listed.json()["jobs"] if item["job_id"] == job_id)
        self.assertEqual(selected["experiment_count"], 1)

    def test_external_experiment_product_consistency_routes_to_keyframe_and_asset_lock(self):
        job_id = self._create_video_generation_job()

        response = self._record_external_experiment(
            job_id,
            product_consistency_score=2,
            storyboard_following_score=5,
            visual_quality_score=5,
            ad_readiness_score=5,
            overall_score=3,
        )

        self.assertEqual(response.status_code, 200)
        job = response.json()["job"]
        self.assertEqual(
            job["external_experiments"][0]["result_url"],
            "https://example.com/gemini-video.mp4",
        )
        decision = job["external_video_experiments"][0]["agent_feedback_decision"]
        self.assertTrue(decision["has_feedback"])
        self.assertEqual(decision["decision_type"], "feedback_rework_requested")
        self.assertEqual(decision["issue_type"], "product_consistency")
        self.assertEqual(decision["target_agent_id"], "keyframe_agent")
        self.assertEqual(decision["secondary_target_agent_id"], "asset_lock_agent")
        self.assertEqual(decision["severity"], "high")
        self.assertTrue(decision["triggered_rework_run_id"])
        self.assertIn("/api/v1/agent-runs/", decision["triggered_rework_poll_url"])
        self.assertEqual(job["latest_experiment_rework_run_id"], decision["triggered_rework_run_id"])
        self.assertEqual(job["latest_rework_artifact_type"], "revised_keyframe_plan")
        self.assertEqual(job["agent_graph_feedback"]["latest_rework_artifact_type"], "revised_keyframe_plan")
        self.assertIn(decision["triggered_rework_run_id"], job["agent_graph_feedback"]["rework_run_ids"])
        self.assertEqual(job["external_video_experiments"][0]["triggered_rework_result_type"], "revised_keyframe_plan")
        self.assertEqual(decision["triggered_rework_result_type"], "revised_keyframe_plan")
        self.assertIn("experiment_feedback_rework_requested", [event["event"] for event in job["history"]])

        rework_run = AGENT_RUN_STORE.get(decision["triggered_rework_run_id"])
        self.assertIsNotNone(rework_run)
        self.assertEqual(rework_run["input_type"], "experiment_feedback_rework")
        self.assertEqual(rework_run["status"], "completed")
        self.assertEqual(rework_run["source_video_job_id"], job_id)
        self.assertEqual(rework_run["active_node_id"], None)
        self.assertFalse(rework_run["waiting_for_user"])
        self.assertFalse(rework_run["external_api_called"])
        self.assertFalse(rework_run["cost_incurred_by_crossgrowth"])
        self.assertIn("revised_keyframe_plan", rework_run["result"])
        revised_plan = rework_run["result"]["revised_keyframe_plan"]
        self.assertEqual(revised_plan["plan_version"], "revised_keyframe_plan_v1")
        self.assertEqual(revised_plan["target_agent_id"], "keyframe_agent")
        self.assertEqual(revised_plan["secondary_target_agent_id"], "asset_lock_agent")
        self.assertTrue(revised_plan["human_review_required"])
        node_statuses = {node["node_id"]: node["status"] for node in rework_run["graph_nodes"]}
        self.assertEqual(node_statuses["experiment_agent"], "complete")
        self.assertEqual(node_statuses["keyframe_agent"], "rework_requested")
        self.assertEqual(node_statuses["asset_lock_agent"], "rework_requested")
        self.assertEqual(rework_run["transition_decisions"][0]["selected_to_node_id"], "keyframe_agent")
        self.assertEqual(rework_run["validation_results"][0]["rework_target"], "keyframe_agent")
        self.assertEqual(rework_run["rework_loops"][0]["source_agent_id"], "experiment_agent")
        self.assertEqual(rework_run["rework_loops"][0]["target_agent_id"], "keyframe_agent")
        self.assertEqual(rework_run["rework_loops"][0]["status"], "requested")
        self.assertIn("experiment_to_keyframe_rework", rework_run["active_edge_ids"])
        event_types = [event["event_type"] for event in rework_run["events"]]
        self.assertIn("graph_initialized", event_types)
        self.assertIn("transition_decision", event_types)
        self.assertIn("experiment_feedback_rework_requested", event_types)
        self.assertIn("rework_requested", event_types)
        self.assertIn("node_started", event_types)
        self.assertIn("node_completed", event_types)
        self.assertIn("revised_keyframe_plan_created", event_types)
        self.assertIn("rework_artifact_created", event_types)
        self.assertIn("graph_completed", event_types)
        self.assertIn("run_completed", event_types)

    def test_external_experiment_storyboard_following_routes_to_prompt_handoff(self):
        job_id = self._create_video_generation_job()

        response = self._record_external_experiment(
            job_id,
            storyboard_following_score=2,
            product_consistency_score=5,
            visual_quality_score=5,
            ad_readiness_score=5,
            overall_score=3,
        )

        self.assertEqual(response.status_code, 200)
        decision = response.json()["job"]["external_video_experiments"][0]["agent_feedback_decision"]
        self.assertEqual(decision["issue_type"], "storyboard_following")
        self.assertEqual(decision["target_agent_id"], "prompt_handoff_agent")
        self.assertEqual(decision["secondary_target_agent_id"], "keyframe_agent")
        rework_run = AGENT_RUN_STORE.get(decision["triggered_rework_run_id"])
        self.assertEqual(rework_run["status"], "completed")
        self.assertEqual(rework_run["result"]["target_agent_id"], "prompt_handoff_agent")
        self.assertIn("experiment_to_prompt_handoff_rework", rework_run["active_edge_ids"])

    def test_external_experiment_ad_readiness_routes_to_storyboard(self):
        job_id = self._create_video_generation_job()

        response = self._record_external_experiment(
            job_id,
            ad_readiness_score=2,
            product_consistency_score=5,
            storyboard_following_score=5,
            visual_quality_score=5,
            overall_score=3,
        )

        self.assertEqual(response.status_code, 200)
        decision = response.json()["job"]["latest_agent_feedback_decision"]
        self.assertEqual(decision["issue_type"], "ad_readiness")
        self.assertEqual(decision["target_agent_id"], "storyboard_agent")
        self.assertEqual(decision["secondary_target_agent_id"], "strategy_agent")
        rework_run = AGENT_RUN_STORE.get(decision["triggered_rework_run_id"])
        self.assertEqual(rework_run["status"], "completed")
        self.assertEqual(rework_run["result"]["target_agent_id"], "storyboard_agent")
        self.assertIn("experiment_to_storyboard_rework", rework_run["active_edge_ids"])

    def test_external_experiment_cost_value_routes_to_cost_agent(self):
        job_id = self._create_video_generation_job()

        response = self._record_external_experiment(
            job_id,
            actual_cost_usd=1.25,
            product_consistency_score=4,
            storyboard_following_score=4,
            visual_quality_score=4,
            ad_readiness_score=4,
            overall_score=3,
        )

        self.assertEqual(response.status_code, 200)
        decision = response.json()["job"]["latest_agent_feedback_decision"]
        self.assertTrue(decision["has_feedback"])
        self.assertEqual(decision["issue_type"], "cost_value")
        self.assertEqual(decision["target_agent_id"], "cost_agent")
        self.assertEqual(decision["secondary_target_agent_id"], "route_selector_agent")
        rework_run = AGENT_RUN_STORE.get(decision["triggered_rework_run_id"])
        self.assertEqual(rework_run["status"], "completed")
        self.assertEqual(rework_run["result"]["target_agent_id"], "cost_agent")
        self.assertIn("experiment_to_cost_rework", rework_run["active_edge_ids"])

    def test_record_external_video_experiment_rejects_invalid_score(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
            },
        ).json()
        job_id = created["job"]["job_id"]

        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/experiments",
            json={
                "tool_name": "gemini",
                "prompt_type": "gemini_video_prompt",
                "overall_score": 6,
            },
            headers={"X-Request-ID": "video-experiment-invalid-score-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-experiment-invalid-score-1")
        self.assertIn("overall_score", payload["error"])
        self.assertIn("between 1 and 5", payload["error"])

    def test_provider_submit_moves_runway_job_to_queued(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
            },
        ).json()
        job_id = created["job"]["job_id"]

        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-submit",
            json={
                "provider_job_id": "runway_scaffold_123",
                "notes": "Submit to simulated provider scaffold.",
            },
            headers={"X-Request-ID": "video-provider-submit-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-provider-submit-1")
        job = payload["job"]
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["provider_runtime"]["provider_job_id"], "runway_scaffold_123")
        self.assertEqual(job["provider_runtime"]["provider_status"], "queued")
        self.assertEqual(job["provider_runtime"]["integration_mode"], "simulated")
        self.assertFalse(job["provider_runtime"]["feature_flag_enabled"])
        self.assertFalse(job["provider_runtime"]["real_external_api_call_enabled"])
        self.assertFalse(job["provider_runtime"]["external_api_called"])
        self.assertEqual(job["result"]["provider_job_id"], "runway_scaffold_123")
        self.assertIn("provider_submitted", [event["event"] for event in job["history"]])
        self.assertIn("status_changed", [event["event"] for event in job["history"]])

    def test_provider_submit_rejects_manual_export_provider(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
            },
        ).json()
        job_id = created["job"]["job_id"]

        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-submit",
            json={},
            headers={"X-Request-ID": "video-provider-submit-manual-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertIn("provider does not support polling scaffold", payload["error"])
        self.assertEqual(payload["request_id"], "video-provider-submit-manual-1")

    def test_provider_submit_returns_404_for_missing_job(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/video_job_missing/provider-submit",
            json={},
            headers={"X-Request-ID": "video-provider-submit-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["request_id"], "video-provider-submit-missing-1")

    def test_provider_poll_before_submit_returns_400(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
            },
        ).json()
        job_id = created["job"]["job_id"]

        response = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-poll",
            json={},
            headers={"X-Request-ID": "video-provider-poll-before-submit-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["request_id"], "video-provider-poll-before-submit-1")
        self.assertIn("provider job has not been submitted", payload["error"])

    def test_provider_poll_moves_queued_to_processing_then_complete(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "pika",
            },
        ).json()
        job_id = created["job"]["job_id"]

        submitted = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-submit",
            json={},
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json()["job"]["status"], "queued")

        processing = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-poll",
            json={},
        )
        self.assertEqual(processing.status_code, 200)
        processing_job = processing.json()["job"]
        self.assertEqual(processing_job["status"], "processing")
        self.assertEqual(processing_job["provider_runtime"]["provider_status"], "processing")
        self.assertEqual(processing_job["provider_runtime"]["poll_count"], 1)
        self.assertIn("provider_polled", [event["event"] for event in processing_job["history"]])

        completed = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-poll",
            json={
                "provider_status": "external_result_ready",
                "result_url": "https://example.com/pika-video.mp4",
                "preview_url": "https://example.com/pika-preview.jpg",
                "download_url": "https://example.com/pika-download.mp4",
                "notes": "Simulated provider result.",
            },
        )
        self.assertEqual(completed.status_code, 200)
        completed_job = completed.json()["job"]
        self.assertEqual(completed_job["status"], "external_result_ready")
        self.assertEqual(completed_job["result"]["result_url"], "https://example.com/pika-video.mp4")
        self.assertEqual(completed_job["result"]["preview_url"], "https://example.com/pika-preview.jpg")
        self.assertEqual(completed_job["result"]["download_url"], "https://example.com/pika-download.mp4")
        self.assertEqual(completed_job["provider_runtime"]["poll_count"], 2)
        self.assertEqual(completed_job["provider_runtime"]["integration_mode"], "simulated")
        self.assertFalse(completed_job["provider_runtime"]["real_external_api_call_enabled"])
        self.assertFalse(completed_job["provider_runtime"]["external_api_called"])

    def test_provider_poll_can_mark_processing_job_failed(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "runway",
            },
        ).json()
        job_id = created["job"]["job_id"]
        self.client.post(f"/api/v1/video-generation/jobs/{job_id}/provider-submit", json={})
        self.client.post(f"/api/v1/video-generation/jobs/{job_id}/provider-poll", json={})

        failed = self.client.post(
            f"/api/v1/video-generation/jobs/{job_id}/provider-poll",
            json={
                "provider_status": "failed",
                "error_message": "simulated provider timeout",
                "notes": "Provider scaffold failure path.",
            },
        )

        self.assertEqual(failed.status_code, 200)
        job = failed.json()["job"]
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["provider_runtime"]["provider_status"], "failed")
        self.assertEqual(job["provider_runtime"]["error_message"], "simulated provider timeout")
        self.assertEqual(job["result"]["error_message"], "simulated provider timeout")

    def test_provider_poll_returns_404_for_missing_job(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/video_job_missing/provider-poll",
            json={},
            headers={"X-Request-ID": "video-provider-poll-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["request_id"], "video-provider-poll-missing-1")

    def test_create_video_generation_job_from_generation_data(self):
        generation_data = {
            "assets": {
                "tiktok_script": {
                    "hook": "Tired of loud blenders?",
                    "cta": "Try this compact option.",
                },
                "storyboard": {
                    "scenes": [
                        {"narration": "Scene one"},
                        {"narration": "Scene two"},
                    ]
                },
            },
            "evaluation": {
                "risk_level": "medium",
                "is_grounded": True,
            },
            "agent_trace": {
                "trace_version": "agent_trace_v1",
            },
            "video_generation_packet": VIDEO_PACKET,
        }

        response = self.client.post(
            "/api/v1/video-generation/jobs/from-generation",
            json={
                "generation_data": generation_data,
                "provider": "pika",
                "output_language": "en",
            },
            headers={"X-Request-ID": "video-job-from-generation-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-from-generation-1")

        job = payload["job"]
        self.assertEqual(job["provider"], "pika")
        self.assertEqual(job["provider_payload"]["selected_export_key"], "pika_style_prompt")
        self.assertEqual(job["source_generation"]["hook"], "Tired of loud blenders?")
        self.assertEqual(job["source_generation"]["storyboard_scene_count"], 2)
        self.assertEqual(job["source_generation"]["risk_level"], "medium")
        self.assertTrue(job["source_generation"]["is_grounded"])
        self.assertEqual(job["source_generation"]["agent_trace_version"], "agent_trace_v1")

    def test_create_video_generation_job_from_generation_rejects_missing_video_packet(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/from-generation",
            json={
                "generation_data": {
                    "assets": {
                        "tiktok_script": {
                            "hook": "Missing packet"
                        }
                    }
                },
                "provider": "manual_export",
            },
            headers={"X-Request-ID": "video-job-from-generation-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-from-generation-invalid-1")
        self.assertIn("generation_data.video_generation_packet", payload["error"])

    def test_create_video_generation_job_from_generation_rejects_unsupported_provider(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs/from-generation",
            json={
                "generation_data": {
                    "video_generation_packet": VIDEO_PACKET
                },
                "provider": "unknown_provider",
            },
            headers={"X-Request-ID": "video-job-from-generation-provider-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-from-generation-provider-invalid-1")
        self.assertIn("unsupported", payload["error"])

    def test_list_video_generation_jobs_returns_recent_summaries(self):
        first = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "capcut",
                "output_language": "en",
            },
        ).json()["job"]

        second = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "pika",
                "output_language": "en",
            },
        ).json()["job"]

        response = self.client.get(
            "/api/v1/video-generation/jobs?limit=10",
            headers={"X-Request-ID": "video-job-list-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-list-1")
        self.assertGreaterEqual(payload["job_count"], 2)

        jobs = payload["jobs"]
        job_ids = {job["job_id"] for job in jobs}
        self.assertIn(first["job_id"], job_ids)
        self.assertIn(second["job_id"], job_ids)

        selected = next(job for job in jobs if job["job_id"] == second["job_id"])
        self.assertEqual(selected["provider"], "pika")
        self.assertEqual(selected["selected_export_key"], "pika_style_prompt")
        self.assertFalse(selected["has_result_url"])

    def test_list_video_generation_jobs_clamps_limit(self):
        response = self.client.get("/api/v1/video-generation/jobs?limit=999")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["limit"], 50)

    def test_get_video_generation_job_returns_created_job(self):
        created = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": VIDEO_PACKET,
                "provider": "manual_export",
                "output_language": "en",
            },
        ).json()

        job_id = created["job"]["job_id"]
        response = self.client.get(
            f"/api/v1/video-generation/jobs/{job_id}",
            headers={"X-Request-ID": "video-job-get-1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["request_id"], "video-job-get-1")
        self.assertEqual(payload["job"]["job_id"], job_id)
        self.assertEqual(payload["job"]["status"], "ready_for_manual_export")

    def test_create_video_generation_job_rejects_wrong_packet_version(self):
        response = self.client.post(
            "/api/v1/video-generation/jobs",
            json={
                "video_generation_packet": {"packet_version": "wrong"},
                "provider": "manual_export",
            },
            headers={"X-Request-ID": "video-job-invalid-1"},
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-invalid-1")
        self.assertIn("video_generation_v1", payload["error"])

    def test_get_video_generation_job_returns_404_for_missing_job(self):
        response = self.client.get(
            "/api/v1/video-generation/jobs/video_job_missing",
            headers={"X-Request-ID": "video-job-missing-1"},
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["request_id"], "video-job-missing-1")


if __name__ == "__main__":
    unittest.main()
