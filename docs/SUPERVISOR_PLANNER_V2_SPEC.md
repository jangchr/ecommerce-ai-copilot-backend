# Supervisor / Planner Agent v2 Spec

## Goal

Supervisor / Planner Agent v2 is the project-level planning agent.

It reads the current project state and tells the user the next best action.

This is not the same as Graph Router Agent.

- Graph Router Agent chooses the next edge inside an active agent graph.
- Supervisor / Planner Agent chooses the next user/system action at the project level.

The product goal remains:

True multi-agent graph collaboration system, not a linear workflow.

---

## Why this agent is needed

The project now has many working parts:

- Project Workspace
- Project Sources
- Source Quality Gate
- Source Evidence Artifact
- Uploaded Product Assets
- Product Asset Lock v2
- Agent Graph OS
- Artifact Registry v2
- Video Jobs
- External Experiments
- Rework Runs
- Human Approval Gate
- Provider Simulation
- Graph Reports
- History

Without a Supervisor / Planner Agent, users must manually decide:

- Should I add a source?
- Should I paste reviews?
- Should I upload a product image?
- Can I start an Agent Run?
- Should I create a Video Job?
- Should I record an experiment?
- Should I use a revised handoff?
- Should I approve provider simulation?
- Should I export a report?

Supervisor / Planner Agent v2 should reduce this confusion by showing one clear next best action.

---

## Inputs

The planner should read these project-scoped inputs when available:

### Project

- project_id
- project_name
- product_name
- product_category
- source_type
- graph_summary

### Source

- latest_source_id
- source_type
- source_status
- source_confidence
- source_summary
- source warnings

### Source Quality Gate

- gate status
- evidence_readiness
- allows_agent_run
- requires_manual_review
- recommended_next_action
- warnings

### Source Evidence Artifact

- evidence_quotes
- review_snippets
- review_classifications
- product_signals
- manual_fallback_needed

### Assets

- uploaded_product_asset
- uploaded_reference_asset
- product_asset_lock_v2
- primary_asset_id
- reference_asset_ids

### Agent Graph

- latest run
- graph_version
- graph events
- graph state snapshot
- rework loops
- graph router decisions

### Artifact Registry v2

- registry_version
- artifacts
- lineage_summary
- revised artifacts
- approval artifacts
- provider result artifacts

### Video Job

- latest_job_id
- provider status
- branch_selected
- external_api_called
- cost_incurred_by_crossgrowth

### Experiments

- first experiment
- second experiment
- comparison result
- experiment feedback decision
- decision gate

### Human Approval

- approval gate status
- approved / rejected / changes_requested / cancelled
- provider blocked or unlocked

---

## Output shape

The planner should return a deterministic object:

planner_recommendation = {
  "planner_version": "supervisor_planner_v2",
  "project_id": "...",
  "overall_status": "needs_source | needs_reviews | source_ready | asset_recommended | ready_for_agent_run | ready_for_video_job | waiting_for_experiment | needs_rework | waiting_for_second_experiment | waiting_for_approval | provider_ready | completed | blocked",
  "next_best_action": "...",
  "next_action_type": "add_source | paste_reviews | upload_asset | start_agent_run | create_video_job | record_experiment | use_revised_handoff | approve_controlled_test | submit_provider_simulation | export_report | review_blocker",
  "next_agent_id": "...",
  "user_action_required": true,
  "can_start_agent_run": false,
  "can_create_video_job": false,
  "can_record_experiment": false,
  "can_request_approval": false,
  "can_submit_provider": false,
  "missing_inputs": [],
  "warnings": [],
  "reasons": [],
  "evidence": {
    "source_quality_gate_status": "...",
    "source_confidence": 0.0,
    "artifact_registry_version": "artifact_registry_v2",
    "latest_run_id": null,
    "latest_job_id": null,
    "latest_experiment_status": null
  },
  "safety_boundaries": {
    "external_api_called": false,
    "cost_incurred_by_crossgrowth": false,
    "llm_autonomous_decision_enabled": false
  }
}

---

## Rule table

### Rule 1: Empty project

Condition:
- No source
- No source evidence artifact
- No agent run

Planner result:
- overall_status = needs_source
- next_action_type = add_source
- next_best_action = Add a product source or paste customer feedback.
- user_action_required = true
- can_start_agent_run = false

Chinese UI:
- 下一步：添加商品来源或粘贴客户反馈。

---

### Rule 2: Amazon / Shopify URL exists but no usable reviews

Condition:
- source_type is amazon_url or shopify_url
- source quality gate is fallback_required or warning
- manual_reviews_recommended exists
- review_count is 0

Planner result:
- overall_status = needs_reviews
- next_action_type = paste_reviews
- next_best_action = Paste customer reviews before starting review-grounded generation.
- user_action_required = true
- can_start_agent_run = false or warning-only true if existing generation supports product-only mode

Chinese UI:
- 下一步：补充客户评论。当前公开来源没有足够评论，不能假装有评论证据。

---

### Rule 3: Pasted reviews ready but no product image

Condition:
- source evidence artifact exists
- source quality gate passed or warning
- review_count >= minimum threshold
- no uploaded product asset

Planner result:
- overall_status = asset_recommended
- next_action_type = upload_asset
- next_best_action = You can start the Agent Run, but uploading a product image is recommended for product consistency.
- user_action_required = false
- can_start_agent_run = true

Chinese UI:
- 下一步：可以开始 Agent Run，但建议先上传商品图，提高产品一致性。

---

### Rule 4: Source and product image are ready

Condition:
- source evidence artifact exists
- source quality gate passed or warning
- product_asset_lock_v2 exists or uploaded product asset exists

Planner result:
- overall_status = ready_for_agent_run
- next_action_type = start_agent_run
- next_best_action = Start Agent Run.
- user_action_required = false
- can_start_agent_run = true

Chinese UI:
- 下一步：开始 Agent Run。

---

### Rule 5: Agent Run completed, no Video Job

Condition:
- latest agent run completed
- video_generation_packet exists
- external_video_tool_handoff exists
- no video job exists

Planner result:
- overall_status = ready_for_video_job
- next_action_type = create_video_job
- next_best_action = Create a Video Job from the handoff.
- can_create_video_job = true

Chinese UI:
- 下一步：基于 handoff 创建 Video Job。

---

### Rule 6: Video Job exists, no experiment recorded

Condition:
- video job exists
- no external experiment recorded

Planner result:
- overall_status = waiting_for_experiment
- next_action_type = record_experiment
- next_best_action = Generate video manually in the external tool, then record experiment results.
- user_action_required = true
- can_record_experiment = true

Chinese UI:
- 下一步：去外部工具手动生成视频，然后记录实验结果。

---

### Rule 7: First experiment is poor and revised artifacts exist

Condition:
- first experiment recorded
- product_consistency or storyboard_following is low
- revised_keyframe_plan or revised_external_video_handoff exists

Planner result:
- overall_status = needs_rework
- next_action_type = use_revised_handoff
- next_best_action = Use the revised external video handoff for a second experiment.
- user_action_required = true

Chinese UI:
- 下一步：使用 revised handoff 再做第二次实验。

---

### Rule 8: Second experiment improved

Condition:
- second experiment comparison exists
- comparison status is improved
- decision gate recommends controlled provider test

Planner result:
- overall_status = waiting_for_approval
- next_action_type = approve_controlled_test
- next_best_action = Review the controlled provider checklist and approve or request changes.
- user_action_required = true
- can_request_approval = true

Chinese UI:
- 下一步：复核 controlled provider checklist，然后批准或要求修改。

---

### Rule 9: Human Approval pending

Condition:
- human_approval_gate status is pending_approval
- provider submit is blocked

Planner result:
- overall_status = waiting_for_approval
- next_action_type = approve_controlled_test
- next_best_action = Approve controlled test or request changes before provider submit.
- user_action_required = true
- can_submit_provider = false

Chinese UI:
- 下一步：先完成审批。审批前 Provider Submit 会被阻断。

---

### Rule 10: Human Approval approved

Condition:
- human approval status is approved
- provider simulation available
- real provider disabled

Planner result:
- overall_status = provider_ready
- next_action_type = submit_provider_simulation
- next_best_action = Submit simulated provider job.
- user_action_required = true
- can_submit_provider = true

Chinese UI:
- 下一步：提交模拟 provider job。不会调用真实外部 API。

---

### Rule 11: Provider result ready

Condition:
- provider result ready
- graph report available

Planner result:
- overall_status = completed
- next_action_type = export_report
- next_best_action = Export the graph report or start another iteration.
- user_action_required = false

Chinese UI:
- 下一步：导出 Graph Report，或开始下一轮优化。

---

### Rule 12: Blocked or unsafe state

Condition:
- missing critical product name
- unsupported source
- source quality gate blocked
- risk rework limit reached
- approval rejected/cancelled
- provider blocked

Planner result:
- overall_status = blocked
- next_action_type = review_blocker
- next_best_action = Review the blocker and provide the missing input or decision.
- user_action_required = true

Chinese UI:
- 下一步：处理阻断原因，补充缺失输入或重新决策。

---

## UI requirements

Add a compact visible panel:

Planner Recommendation

Visible fields:
- Current project status
- Next best action
- Why
- Missing inputs
- Human action required
- Safety boundary

Details collapsed:
- full planner object
- source evidence
- artifact evidence
- graph history evidence
- raw decision reasons

Button gating:
- Start Agent Run button should use can_start_agent_run.
- Create Video Job should use can_create_video_job.
- Record Experiment should use can_record_experiment.
- Provider Submit should use can_submit_provider.
- Export Report should remain available when report exists.

---

## Safety boundaries

Supervisor / Planner Agent v2 must never directly call external video APIs.

It must preserve:
- external_api_called = false
- cost_incurred_by_crossgrowth = false
- llm_autonomous_decision_enabled = false

It can recommend actions, but high-risk/cost/provider actions remain gated by Human Approval and provider simulation rules.

---

## Test scenarios

1. Empty project recommends add_source.
2. Amazon URL without reviews recommends paste_reviews.
3. Pasted reviews without product image allows agent run but recommends upload_asset.
4. Source and image ready recommends start_agent_run.
5. Completed agent run without job recommends create_video_job.
6. Job without experiment recommends record_experiment.
7. Bad first experiment recommends use_revised_handoff.
8. Improved second experiment recommends approve_controlled_test.
9. Approval pending blocks provider submit.
10. Approval approved allows simulated provider submit.
11. Provider result ready recommends export_report.
12. Blocked source quality gate recommends review_blocker.

---

## Implementation notes for later Codex batch

Preferred backend helper:

build_supervisor_planner_recommendation(
    project: dict | None = None,
    source: dict | None = None,
    source_quality_gate: dict | None = None,
    source_evidence_artifact: dict | None = None,
    artifact_registry: dict | None = None,
    latest_run: dict | None = None,
    latest_job: dict | None = None,
    latest_experiment: dict | None = None,
    approval_gate: dict | None = None,
) -> dict

Suggested endpoints:

GET /api/v1/projects/{project_id}/planner/recommendation
POST /api/v1/projects/{project_id}/planner/recommendation/refresh

Suggested frontend:

renderPlannerRecommendation(projectSummary)

Suggested artifact:

planner_recommendation_v2

Suggested registry lineage:

project_workspace
→ project_source
→ source_quality_gate
→ source_evidence_artifact
→ supervisor_planner_recommendation
→ agent_graph_run

---

## Definition of done

- Planner recommendation exists for every project.
- Default project works.
- Empty project shows add source.
- Source-only project shows whether reviews/assets are missing.
- Ready project shows Start Agent Run.
- Completed run shows Create Video Job.
- Job without experiment shows Record Experiment.
- Bad experiment shows Use Revised Handoff.
- Improved experiment shows Approval.
- Approval pending blocks provider.
- Approval approved allows simulated provider.
- Provider complete shows Export Report.
- UI is compact and not text-heavy.
- Details are collapsed by default.
- Existing Agent Graph OS smoke still passes.
- external_api_called remains false.
- cost_incurred_by_crossgrowth remains false.
- LLM autonomous decision remains disabled.
