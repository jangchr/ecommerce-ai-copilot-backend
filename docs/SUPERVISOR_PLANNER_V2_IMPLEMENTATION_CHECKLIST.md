# Supervisor / Planner Agent v2 Implementation Checklist

## Purpose

This checklist turns `docs/SUPERVISOR_PLANNER_V2_SPEC.md` into an implementation plan.

Supervisor / Planner Agent v2 should become the project-level decision layer. It should not replace Graph Router Agent.

- Supervisor / Planner Agent decides the project-level next best action.
- Graph Router Agent decides graph-level routing between agents.
- Human Approval Gate still blocks risky/provider actions.
- Provider simulation remains safe.
- External API calls remain disabled.

---

## Implementation phases

### Phase 1 — Backend helper

Add a deterministic helper:

`build_supervisor_planner_recommendation(...)`

Preferred location:
- `agent_runs.py` if keeping all graph helpers together
- or a new file only if needed and Dockerfile already covers it

Inputs:
- project
- source
- source_quality_gate
- source_evidence_artifact
- uploaded assets
- artifact_registry
- latest_run
- latest_job
- latest_experiment
- approval_gate
- provider state
- graph history / snapshots if available

Output:
- planner_version
- project_id
- overall_status
- next_best_action
- next_action_type
- next_agent_id
- user_action_required
- action booleans
- missing_inputs
- warnings
- reasons
- evidence
- safety_boundaries

Safety:
- external_api_called=false
- cost_incurred_by_crossgrowth=false
- llm_autonomous_decision_enabled=false

---

### Phase 2 — Project planner endpoints

Add endpoints:

`GET /api/v1/projects/{project_id}/planner/recommendation`

`POST /api/v1/projects/{project_id}/planner/recommendation/refresh`

Behavior:
- Return current recommendation from project state.
- If project does not exist, return safe not-found response.
- If project exists but has no source, return `needs_source`.
- Do not mutate core graph state except optional planner snapshot/artifact if safe.
- Do not require external APIs.
- Do not require LLM.

---

### Phase 3 — Planner artifact

Add artifact:

`planner_recommendation_v2`

Store in Artifact Registry v2 when safe.

Suggested lineage:

project_workspace
→ project_source
→ source_quality_gate
→ source_evidence_artifact
→ planner_recommendation_v2
→ agent_graph_run

If no source exists:

project_workspace
→ planner_recommendation_v2

---

### Phase 4 — Project summary integration

Add planner fields to project graph summary when safe:

- latest_planner_status
- latest_next_action_type
- latest_next_best_action
- latest_planner_recommendation_id
- can_start_agent_run
- can_create_video_job
- can_record_experiment
- can_submit_provider

---

### Phase 5 — Frontend Planner panel

Add compact panel:

`Planner Recommendation`

Visible by default:
- Current project status
- Next best action
- Why
- Missing inputs
- Human action required
- Safety boundary

Collapsed details:
- full planner object
- evidence fields
- source evidence
- artifact evidence
- graph history evidence
- raw reasons

Button gating:
- Start Agent Run should reflect `can_start_agent_run`
- Create Video Job should reflect `can_create_video_job`
- Record Experiment should reflect `can_record_experiment`
- Provider Submit should reflect `can_submit_provider`

Do not hide buttons completely. Prefer disabled state + clear reason.

---

### Phase 6 — i18n labels

Add EN/ZH labels:

- Planner Recommendation
- Current project status
- Next best action
- Why this action
- Missing inputs
- Human action required
- Can start Agent Run
- Can create Video Job
- Can record experiment
- Can submit provider
- Planner details
- Source is missing
- Reviews are missing
- Product image recommended
- Ready for Agent Run
- Ready for Video Job
- Waiting for experiment
- Rework recommended
- Waiting for approval
- Provider simulation ready
- Export report
- Blocked reason

No `????`.

---

## Required rule coverage

### 1. Empty project

Expected:
- overall_status=needs_source
- next_action_type=add_source
- can_start_agent_run=false

### 2. Amazon / Shopify source without reviews

Expected:
- overall_status=needs_reviews
- next_action_type=paste_reviews
- warning includes manual_reviews_recommended
- can_start_agent_run=false or warning-only true only if product-only mode is intentionally allowed

### 3. Pasted reviews ready but no product image

Expected:
- overall_status=asset_recommended
- next_action_type=upload_asset
- can_start_agent_run=true

### 4. Source and product image ready

Expected:
- overall_status=ready_for_agent_run
- next_action_type=start_agent_run
- can_start_agent_run=true

### 5. Agent Run complete, no Video Job

Expected:
- overall_status=ready_for_video_job
- next_action_type=create_video_job
- can_create_video_job=true

### 6. Video Job exists, no experiment

Expected:
- overall_status=waiting_for_experiment
- next_action_type=record_experiment
- can_record_experiment=true

### 7. Bad first experiment with revised artifact

Expected:
- overall_status=needs_rework
- next_action_type=use_revised_handoff

### 8. Improved second experiment

Expected:
- overall_status=waiting_for_approval
- next_action_type=approve_controlled_test
- can_request_approval=true

### 9. Approval pending

Expected:
- overall_status=waiting_for_approval
- can_submit_provider=false

### 10. Approval approved

Expected:
- overall_status=provider_ready
- next_action_type=submit_provider_simulation
- can_submit_provider=true

### 11. Provider result ready

Expected:
- overall_status=completed
- next_action_type=export_report

### 12. Blocked state

Expected:
- overall_status=blocked
- next_action_type=review_blocker
- user_action_required=true

---

## Backend tests to add later

Suggested file:
- `tests/test_supervisor_planner.py`

Test groups:

1. Helper rule tests
2. Endpoint tests
3. Artifact Registry v2 lineage tests
4. Project summary tests
5. Existing flow compatibility tests

Required assertions:
- default project still works
- no-source project returns needs_source
- source warning returns needs_reviews
- ready source returns can_start_agent_run=true
- completed run returns can_create_video_job=true
- pending approval blocks provider
- approved approval allows simulated provider only
- safety boundaries remain false
- no external API calls
- no LLM autonomy

---

## Frontend tests to add later

Update:
- `tests/test_frontend_probe_boundary.py`

Markers:
- Planner Recommendation
- Current project status
- Next best action
- Why this action
- Missing inputs
- Human action required
- Can start Agent Run
- Can create Video Job
- Can record experiment
- Can submit provider
- Planner details
- Source is missing
- Reviews are missing
- Product image recommended
- Ready for Agent Run
- Ready for Video Job
- Waiting for experiment
- Rework recommended
- Waiting for approval
- Provider simulation ready
- Export report
- Blocked reason

---

## Public smoke additions after implementation

Update smoke script to check:

- planner_recommendation_marker
- planner_empty_project_needs_source
- planner_source_ready
- planner_can_start_agent_run
- planner_video_job_next_action
- planner_experiment_next_action
- planner_approval_pending_blocks_provider
- planner_provider_ready_after_approval
- planner_export_report_after_provider_result
- planner_safety_boundaries_false

---

## Definition of done

Supervisor / Planner Agent v2 is done when:

- Every project can return a planner recommendation.
- The recommendation is deterministic.
- The default demo project still works.
- Source Intelligence flow still works.
- Agent Graph OS smoke still works.
- Project Workspace smoke still works.
- Provider simulation remains safe.
- UI shows one clear next best action.
- Details remain collapsed by default.
- `external_api_called=false`.
- `cost_incurred_by_crossgrowth=false`.
- `llm_autonomous_decision_enabled=false`.
