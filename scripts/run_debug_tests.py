import json
import subprocess
import sys
import time
import csv
import os
import shutil
from datetime import datetime
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TESTS = [
    "https://test.local/products/balsamic_vinegar",
    "https://test.local/products/printer",
    "https://test.local/products/women_bras",
    "https://test.local/products/girls_overalls",
    "https://test.local/products/protein_powder",
    "https://test.local/products/phone_case",
    "https://test.local/products/desk_lamp",
    "https://test.local/products/baby_stroller",
    "https://test.local/products/pet_hair_vacuum",
    "https://test.local/products/skincare_serum",
]

MIN_REVIEW_CONF = 0.70
MIN_REVIEW_COUNT = 5
MIN_EVIDENCE_ALIGNMENT = 0.50
MIN_GROUNDED_CTR = 0.04
MAX_REVISION_COUNT = 2
BASE_URL = "http://127.0.0.1:8001"
BASELINE_REPORT = Path("runs/baselines/l9_2/regression_summary.csv")
LEGACY_BASELINE_REPORT = Path("runs/l9_1_regression_report.csv")
CTR_WARNING_DROP = 0.01
CTR_FAIL_DROP = 0.015
DEFAULT_COST_PER_1K_TOKENS_USD = 0.0005
COST_GATE_LIMITS = {
    "total_tokens": 135000,
    "total_latency_ms": 700000,
    "storyboard_tokens": 45000,
    "strategy_tokens": 35000,
    "cognitive_synthesis_tokens": 35000,
    "analysis_dopamine_tokens": 5000,
}
COST_GATE_WARNING_LIMITS = {
    "total_latency_ms": 650000,
}


def assert_baseline(name, data):
    evidence = data.get("evidence") or {}
    metrics = data.get("world_metrics") or {}
    assert evidence.get("review_confidence", 0) >= MIN_REVIEW_CONF, f"{name}: review_conf too low"
    assert evidence.get("review_count", 0) >= MIN_REVIEW_COUNT, f"{name}: review_count too low"
    assert metrics.get("evidence_alignment", 0) >= MIN_EVIDENCE_ALIGNMENT, f"{name}: evidence_alignment too low"
    assert metrics.get("grounded_ctr", 0) >= MIN_GROUNDED_CTR, f"{name}: grounded_ctr too low"
    assert data.get("revision_count", 0) <= MAX_REVISION_COUNT, f"{name}: too many revisions"


def result_row(name, data, baseline=None):
    evidence = data.get("evidence") or {}
    metrics = data.get("world_metrics") or {}
    baseline = baseline or {}
    grounded_ctr = float(metrics.get("grounded_ctr", 0) or 0)
    evidence_alignment = float(metrics.get("evidence_alignment", 0) or 0)
    revision_count = int(data.get("revision_count", 0) or 0)
    baseline_grounded_ctr = float(baseline.get("grounded_ctr") or 0)
    baseline_evidence_alignment = float(baseline.get("evidence_alignment") or 0)
    baseline_revision_count = int(float(baseline.get("revision_count") or 0))
    delta_grounded_ctr = grounded_ctr - baseline_grounded_ctr if baseline else 0.0
    delta_evidence_alignment = evidence_alignment - baseline_evidence_alignment if baseline else 0.0
    delta_revision_count = revision_count - baseline_revision_count if baseline else 0
    diff_status = "OK"
    diff_warning = ""
    if baseline:
        if delta_grounded_ctr <= -CTR_FAIL_DROP:
            diff_status = "FAIL" if grounded_ctr < MIN_GROUNDED_CTR else "WARN"
            diff_warning = (
                f"grounded_ctr dropped by {abs(delta_grounded_ctr):.4f} "
                f"({baseline_grounded_ctr:.4f} -> {grounded_ctr:.4f})"
            )
        elif delta_grounded_ctr <= -CTR_WARNING_DROP:
            diff_status = "WARN"
            diff_warning = (
                f"grounded_ctr dropped by {abs(delta_grounded_ctr):.4f} "
                f"({baseline_grounded_ctr:.4f} -> {grounded_ctr:.4f})"
            )

    return {
        "category": name,
        "product_category": data.get("product_category", ""),
        "source_type": evidence.get("source_type", ""),
        "review_confidence": evidence.get("review_confidence", 0),
        "trend_confidence": evidence.get("trend_confidence", 0),
        "review_count": evidence.get("review_count", 0),
        "evidence_alignment": evidence_alignment,
        "grounded_ctr": grounded_ctr,
        "is_grounded": metrics.get("is_grounded", False),
        "failure_type": metrics.get("failure_type", ""),
        "regenerate_node": data.get("regenerate_node") or "",
        "revision_count": revision_count,
        "baseline_grounded_ctr": baseline_grounded_ctr,
        "delta_grounded_ctr": delta_grounded_ctr,
        "baseline_evidence_alignment": baseline_evidence_alignment,
        "delta_evidence_alignment": delta_evidence_alignment,
        "baseline_revision_count": baseline_revision_count,
        "delta_revision_count": delta_revision_count,
        "diff_status": diff_status,
        "diff_warning": diff_warning,
        "result": "PASS",
    }


def telemetry_rows(category, data):
    rows = []
    for node_name, metrics in (data.get("telemetry") or {}).items():
        source_traces = metrics.get("source_traces", []) or []
        rows.append(
            {
                "category": category,
                "node": node_name,
                "latency_ms": metrics.get("latency_ms", 0),
                "total_tokens": metrics.get("total_tokens", 0),
                "reasoning_latency_ms": metrics.get("reasoning_latency_ms", 0),
                "status": metrics.get("status", ""),
                "error": metrics.get("error") or "",
                "retries": metrics.get("retries", 0),
                "model": metrics.get("model", ""),
                "role_key": metrics.get("role_key", ""),
                "node_name": metrics.get("node_name", node_name),
                "input_size_char": metrics.get("input_size_char", 0),
                "memory_context_used": metrics.get("memory_context_used", False),
                "evidence_count": metrics.get("evidence_count", 0),
                "trend_signal_count": metrics.get("trend_signal_count", 0),
                "fallback": metrics.get("fallback", False),
                "fallback_indicators": ";".join(metrics.get("fallback_indicators", [])),
                "memory_write_count": metrics.get("memory_write_count", 0),
                "memory_skipped_count": metrics.get("memory_skipped_count", 0),
                "memory_retrieval_count": metrics.get("memory_retrieval_count", 0),
                "memory_retrieval_hits_success": metrics.get("memory_retrieval_hits_success", 0),
                "memory_retrieval_hits_failure": metrics.get("memory_retrieval_hits_failure", 0),
                "memory_record_count_success": metrics.get("memory_record_count_success", 0),
                "memory_record_count_failure": metrics.get("memory_record_count_failure", 0),
                "memory_record_count_total": metrics.get("memory_record_count_total", 0),
                "memory_backend": metrics.get("memory_backend", ""),
                "memory_faiss_error": metrics.get("memory_faiss_error", ""),
                "memory_max_record_count": metrics.get("memory_max_record_count", 0),
                "memory_peak_record_count": metrics.get("memory_peak_record_count", 0),
                "memory_remaining_capacity": metrics.get("memory_remaining_capacity", 0),
                "memory_limit_reached": metrics.get("memory_limit_reached", False),
                "memory_limit_reached_count": metrics.get("memory_limit_reached_count", 0),
                "memory_pruned_count": metrics.get("memory_pruned_count", 0),
                "faiss_fallback_count": metrics.get("faiss_fallback_count", 0),
                "faiss_recovery_count": metrics.get("faiss_recovery_count", 0),
                "faiss_fallback_trace": json.dumps(
                    metrics.get("faiss_fallback_trace", []), ensure_ascii=False
                ),
                "adapter_names": ";".join(str(trace.get("adapter_name", "")) for trace in source_traces),
                "source_names": ";".join(str(trace.get("source_name", "")) for trace in source_traces),
                "adapter_enabled": ";".join(str(trace.get("enabled", False)) for trace in source_traces),
                "adapter_fallback": ";".join(str(trace.get("fallback", False)) for trace in source_traces),
                "adapter_fallback_reason": ";".join(str(trace.get("fallback_reason", "")) for trace in source_traces),
                "adapter_fetch_latency_ms": sum(float(trace.get("fetch_latency_ms", 0) or 0) for trace in source_traces),
                "adapter_source_type": ";".join(str(trace.get("source_type", "")) for trace in source_traces),
                "adapter_confidence": ";".join(str(trace.get("confidence", 0)) for trace in source_traces),
            }
        )
    return rows


def cost_per_1k_tokens():
    raw = os.getenv("LLM_COST_PER_1K_TOKENS_USD", "")
    if not raw:
        return DEFAULT_COST_PER_1K_TOKENS_USD
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_COST_PER_1K_TOKENS_USD


def add_cost_fields(rows):
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in rows)
    total_latency = sum(float(row.get("total_latency_ms") or 0) for row in rows)
    unit_cost = cost_per_1k_tokens()
    enriched = []
    for row in rows:
        item = row.copy()
        tokens = int(item.get("total_tokens") or 0)
        latency = float(item.get("total_latency_ms") or 0)
        item["cost_per_1k_tokens_usd"] = unit_cost
        item["estimated_cost_usd"] = tokens / 1000 * unit_cost
        item["token_share"] = tokens / total_tokens if total_tokens else 0
        item["latency_share"] = latency / total_latency if total_latency else 0
        enriched.append(item)
    return enriched


def telemetry_aggregate(rows):
    by_category = {}
    for row in rows:
        category = row["category"]
        item = by_category.setdefault(
            category,
            {
                "category": category,
                "total_latency_ms": 0.0,
                "total_tokens": 0,
                "failed_nodes": "",
                "node_count": 0,
            },
        )
        item["total_latency_ms"] += float(row.get("latency_ms") or 0)
        item["total_tokens"] += int(row.get("total_tokens") or 0)
        item["node_count"] += 1
        if row.get("status") != "success":
            failed = item["failed_nodes"].split(";") if item["failed_nodes"] else []
            failed.append(row.get("node", "unknown"))
            item["failed_nodes"] = ";".join(failed)
    return add_cost_fields(list(by_category.values()))


def telemetry_node_aggregate(rows):
    by_node = {}
    for row in rows:
        node = row["node"]
        item = by_node.setdefault(
            node,
            {
                "node": node,
                "total_latency_ms": 0.0,
                "total_tokens": 0,
                "total_reasoning_latency_ms": 0.0,
                "total_input_size_char": 0,
                "memory_context_used_count": 0,
                "total_evidence_count": 0,
                "total_trend_signal_count": 0,
                "fallback_count": 0,
                "fallback_indicators": "",
                "max_memory_write_count": 0,
                "max_memory_skipped_count": 0,
                "max_memory_retrieval_count": 0,
                "max_memory_retrieval_hits_success": 0,
                "max_memory_retrieval_hits_failure": 0,
                "max_memory_record_count_total": 0,
                "max_memory_record_limit": 0,
                "max_memory_peak_record_count": 0,
                "min_memory_remaining_capacity": None,
                "memory_limit_reached_count": 0,
                "max_memory_pruned_count": 0,
                "max_faiss_fallback_count": 0,
                "max_faiss_recovery_count": 0,
                "memory_backends": "",
                "memory_faiss_errors": "",
                "faiss_fallback_traces": "",
                "adapter_fetch_latency_ms": 0.0,
                "adapter_fallback_count": 0,
                "adapter_names": "",
                "source_names": "",
                "adapter_enabled_states": "",
                "adapter_fallback_reasons": "",
                "adapter_source_types": "",
                "adapter_confidences": "",
                "failed_count": 0,
                "run_count": 0,
            },
        )
        item["total_latency_ms"] += float(row.get("latency_ms") or 0)
        item["total_tokens"] += int(row.get("total_tokens") or 0)
        item["total_reasoning_latency_ms"] += float(row.get("reasoning_latency_ms") or 0)
        item["total_input_size_char"] += int(row.get("input_size_char") or 0)
        item["memory_context_used_count"] += int(bool(row.get("memory_context_used")))
        item["total_evidence_count"] += int(row.get("evidence_count") or 0)
        item["total_trend_signal_count"] += int(row.get("trend_signal_count") or 0)
        if row.get("fallback"):
            item["fallback_count"] += 1
            indicators = [
                value for value in str(row.get("fallback_indicators") or "").split(";") if value
            ]
            known = [
                value for value in item["fallback_indicators"].split(";") if value
            ]
            item["fallback_indicators"] = ";".join(dict.fromkeys(known + indicators))
        for output_name, source_name in (
            ("max_memory_write_count", "memory_write_count"),
            ("max_memory_skipped_count", "memory_skipped_count"),
            ("max_memory_retrieval_count", "memory_retrieval_count"),
            ("max_memory_retrieval_hits_success", "memory_retrieval_hits_success"),
            ("max_memory_retrieval_hits_failure", "memory_retrieval_hits_failure"),
            ("max_memory_record_count_total", "memory_record_count_total"),
            ("max_memory_record_limit", "memory_max_record_count"),
            ("max_memory_peak_record_count", "memory_peak_record_count"),
            ("memory_limit_reached_count", "memory_limit_reached_count"),
            ("max_memory_pruned_count", "memory_pruned_count"),
            ("max_faiss_fallback_count", "faiss_fallback_count"),
            ("max_faiss_recovery_count", "faiss_recovery_count"),
        ):
            item[output_name] = max(item[output_name], int(row.get(source_name) or 0))
        remaining_capacity = int(row.get("memory_remaining_capacity") or 0)
        if row.get("memory_max_record_count"):
            if item["min_memory_remaining_capacity"] is None:
                item["min_memory_remaining_capacity"] = remaining_capacity
            else:
                item["min_memory_remaining_capacity"] = min(
                    item["min_memory_remaining_capacity"], remaining_capacity
                )
        backends = [value for value in item["memory_backends"].split(";") if value]
        if row.get("memory_backend"):
            item["memory_backends"] = ";".join(dict.fromkeys(backends + [row["memory_backend"]]))
        errors = [value for value in item["memory_faiss_errors"].split(";") if value]
        if row.get("memory_faiss_error"):
            item["memory_faiss_errors"] = ";".join(dict.fromkeys(errors + [row["memory_faiss_error"]]))
        if row.get("faiss_fallback_trace") and row["faiss_fallback_trace"] != "[]":
            # Counters preserve history; the latest bounded trace keeps the CSV readable.
            item["faiss_fallback_traces"] = row["faiss_fallback_trace"]
        item["adapter_fetch_latency_ms"] += float(row.get("adapter_fetch_latency_ms") or 0)
        fallback_values = [
            value for value in str(row.get("adapter_fallback") or "").split(";") if value
        ]
        item["adapter_fallback_count"] += sum(value == "True" for value in fallback_values)
        adapter_names = [value for value in item["adapter_names"].split(";") if value]
        current_adapters = [value for value in str(row.get("adapter_names") or "").split(";") if value]
        item["adapter_names"] = ";".join(dict.fromkeys(adapter_names + current_adapters))
        for aggregate_name, row_name in (
            ("source_names", "source_names"),
            ("adapter_enabled_states", "adapter_enabled"),
            ("adapter_fallback_reasons", "adapter_fallback_reason"),
            ("adapter_source_types", "adapter_source_type"),
            ("adapter_confidences", "adapter_confidence"),
        ):
            current_values = [
                value for value in str(row.get(row_name) or "").split(";") if value
            ]
            known_values = [
                value for value in item[aggregate_name].split(";") if value
            ]
            item[aggregate_name] = ";".join(dict.fromkeys(known_values + current_values))
        item["run_count"] += 1
        if row.get("status") != "success":
            item["failed_count"] += 1
    return add_cost_fields(list(by_node.values()))


def cost_gate_rows(telemetry_summary, node_summary):
    node_by_name = {row["node"]: row for row in node_summary}
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in telemetry_summary)
    total_latency_ms = sum(float(row.get("total_latency_ms") or 0) for row in telemetry_summary)
    failed_nodes = [
        row["category"] for row in telemetry_summary if row.get("failed_nodes")
    ]
    actuals = {
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency_ms,
        "storyboard_tokens": int(node_by_name.get("storyboard", {}).get("total_tokens") or 0),
        "strategy_tokens": int(node_by_name.get("strategy", {}).get("total_tokens") or 0),
        "cognitive_synthesis_tokens": int(
            node_by_name.get("cognitive_synthesis", {}).get("total_tokens") or 0
        ),
        "analysis_dopamine_tokens": int(
            node_by_name.get("analysis_dopamine", {}).get("total_tokens") or 0
        ),
    }
    rows = []
    for metric, limit in COST_GATE_LIMITS.items():
        actual = actuals[metric]
        warning_limit = COST_GATE_WARNING_LIMITS.get(metric, "")
        status = "PASS"
        if actual > limit:
            status = "FAIL"
        elif warning_limit != "" and actual > warning_limit:
            status = "WARN"
        rows.append(
            {
                "metric": metric,
                "actual": actual,
                "warning_limit": warning_limit,
                "limit": limit,
                "status": status,
            }
        )
    rows.append(
        {
            "metric": "failed_nodes",
            "actual": ";".join(failed_nodes) if failed_nodes else "None",
            "warning_limit": "",
            "limit": "None",
            "status": "PASS" if not failed_nodes else "FAIL",
        }
    )
    return rows


def assert_cost_gate(rows):
    failed = [row for row in rows if row["status"] == "FAIL"]
    if failed:
        details = ", ".join(
            f"{row['metric']}={row['actual']} (limit {row['limit']})" for row in failed
        )
        raise AssertionError(f"Cost gate failed: {details}")


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_baseline(path):
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {row["category"]: row for row in csv.DictReader(handle)}


def compare_with_baseline(rows):
    baseline_path = BASELINE_REPORT if BASELINE_REPORT.exists() else LEGACY_BASELINE_REPORT
    baseline = load_baseline(baseline_path)
    warnings = []
    for row in rows:
        if row.get("diff_status") == "WARN":
            warnings.append(f"{row['category']}: {row.get('diff_warning')}")
        elif row.get("diff_status") == "FAIL":
            raise AssertionError(f"{row['category']}: {row.get('diff_warning')}")

        prior = baseline.get(row["category"])
        if not prior:
            continue
        baseline_alignment = float(prior.get("evidence_alignment") or 0)
        current_alignment = float(row["evidence_alignment"] or 0)
        if baseline_alignment >= 1.0 and current_alignment < MIN_EVIDENCE_ALIGNMENT:
            raise AssertionError(
                f"{row['category']}: evidence_alignment regressed from "
                f"{baseline_alignment:.2f} to {current_alignment:.2f}"
            )
    return warnings


def write_markdown_report(path, rows, warnings, telemetry_summary, cost_gate):
    telemetry_by_category = {row["category"]: row for row in telemetry_summary}
    total_latency_ms = sum(float(row.get("total_latency_ms") or 0) for row in telemetry_summary)
    total_tokens = sum(int(row.get("total_tokens") or 0) for row in telemetry_summary)
    failed_nodes = [
        f"{row['category']}:{row['failed_nodes']}"
        for row in telemetry_summary
        if row.get("failed_nodes")
    ]
    lines = [
        "# L9 Regression Run",
        "",
        f"Generated at `{datetime.now().isoformat(timespec='seconds')}`.",
        "",
        "## Telemetry",
        "",
        f"- Total latency: {total_latency_ms:.0f} ms",
        f"- Total tokens: {total_tokens}",
        f"- Estimated cost: ${sum(float(row.get('estimated_cost_usd') or 0) for row in telemetry_summary):.4f}",
        f"- Failed nodes: {', '.join(failed_nodes) if failed_nodes else 'None'}",
        "",
        "## Cost Gate",
        "",
        "| Metric | Actual | Warning Limit | Fail Limit | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    lines.extend(
        f"| {row['metric']} | {row['actual']} | {row['warning_limit']} | {row['limit']} | {row['status']} |"
        for row in cost_gate
    )
    lines.extend(
        [
        "",
        "## Diff Warnings",
        "",
        ]
    )
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Results",
            "",
            "| Category | Review Conf | Review Count | Evidence Alignment | Grounded CTR | Grounded | Failure Type | Revisions | Result |",
            "| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {category} | {review_confidence:.2f} | {review_count} | "
            "{evidence_alignment:.2f} | {grounded_ctr:.4f} | {is_grounded} | "
            "{failure_type} | {revision_count} | {result} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Category Telemetry",
            "",
            "| Category | Total Latency Ms | Total Tokens | Estimated Cost USD | Token Share | Latency Share | Failed Nodes |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        summary = telemetry_by_category.get(row["category"], {})
        lines.append(
            "| {category} | {total_latency_ms:.0f} | {total_tokens} | {estimated_cost_usd:.4f} | {token_share:.2%} | {latency_share:.2%} | {failed_nodes} |".format(
                category=row["category"],
                total_latency_ms=float(summary.get("total_latency_ms") or 0),
                total_tokens=int(summary.get("total_tokens") or 0),
                estimated_cost_usd=float(summary.get("estimated_cost_usd") or 0),
                token_share=float(summary.get("token_share") or 0),
                latency_share=float(summary.get("latency_share") or 0),
                failed_nodes=summary.get("failed_nodes") or "",
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    server_process = None
    output_dir = Path("runs")
    latest_dir = output_dir / "latest"
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_dir = output_dir / "history" / run_id
    result_rows = []
    all_telemetry_rows = []
    output_dir.mkdir(exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = BASELINE_REPORT if BASELINE_REPORT.exists() else LEGACY_BASELINE_REPORT
    baseline = load_baseline(baseline_path)
    try:
        requests.get(f"{BASE_URL}/docs", timeout=3)
    except requests.RequestException:
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8001",
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            try:
                requests.get(f"{BASE_URL}/docs", timeout=3).raise_for_status()
                break
            except requests.RequestException:
                time.sleep(1)
        else:
            raise RuntimeError("Could not start local debug API server.")

    try:
        for url in TESTS:
            payload = {"url": url, "goal": "tiktok_ctr"}
            response = requests.post(
                f"{BASE_URL}/api/v1/debug-copilot",
                json=payload,
                timeout=600,
            )
            response.raise_for_status()
            data = response.json()
            name = url.rstrip("/").split("/")[-1]
            payload_text = json.dumps(data, ensure_ascii=False, indent=2)
            (output_dir / f"{name}.json").write_text(payload_text, encoding="utf-8")
            (latest_dir / f"{name}.json").write_text(payload_text, encoding="utf-8")
            (history_dir / f"{name}.json").write_text(payload_text, encoding="utf-8")
            assert_baseline(name, data)
            result_rows.append(result_row(name, data, baseline.get(name)))
            all_telemetry_rows.extend(telemetry_rows(name, data))
            metrics = data.get("world_metrics", {})
            evidence = data.get("evidence") or {}
            print(
                name,
                {
                    "review_conf": evidence.get("review_confidence"),
                    "review_count": evidence.get("review_count"),
                    "evidence_alignment": metrics.get("evidence_alignment"),
                    "grounded_ctr": metrics.get("grounded_ctr"),
                    "failure_type": metrics.get("failure_type"),
                    "regenerate_node": data.get("regenerate_node"),
                    "revision_count": data.get("revision_count"),
                },
            )
        warnings = compare_with_baseline(result_rows)
        result_fields = [
            "category",
            "product_category",
            "source_type",
            "review_confidence",
            "trend_confidence",
            "review_count",
            "evidence_alignment",
            "grounded_ctr",
            "is_grounded",
            "failure_type",
            "regenerate_node",
            "revision_count",
            "baseline_grounded_ctr",
            "delta_grounded_ctr",
            "baseline_evidence_alignment",
            "delta_evidence_alignment",
            "baseline_revision_count",
            "delta_revision_count",
            "diff_status",
            "diff_warning",
            "result",
        ]
        telemetry_fields = [
            "category",
            "node",
            "latency_ms",
            "total_tokens",
            "reasoning_latency_ms",
            "status",
            "error",
            "retries",
            "model",
            "role_key",
            "node_name",
            "input_size_char",
            "memory_context_used",
            "evidence_count",
            "trend_signal_count",
            "fallback",
            "fallback_indicators",
            "memory_write_count",
            "memory_skipped_count",
            "memory_retrieval_count",
            "memory_retrieval_hits_success",
            "memory_retrieval_hits_failure",
            "memory_record_count_success",
            "memory_record_count_failure",
            "memory_record_count_total",
            "memory_backend",
            "memory_faiss_error",
            "memory_max_record_count",
            "memory_peak_record_count",
            "memory_remaining_capacity",
            "memory_limit_reached",
            "memory_limit_reached_count",
            "memory_pruned_count",
            "faiss_fallback_count",
            "faiss_recovery_count",
            "faiss_fallback_trace",
            "adapter_names",
            "source_names",
            "adapter_enabled",
            "adapter_fallback",
            "adapter_fallback_reason",
            "adapter_fetch_latency_ms",
            "adapter_source_type",
            "adapter_confidence",
        ]
        telemetry_aggregate_rows = telemetry_aggregate(all_telemetry_rows)
        telemetry_aggregate_fields = [
            "category",
            "total_latency_ms",
            "total_tokens",
            "cost_per_1k_tokens_usd",
            "estimated_cost_usd",
            "token_share",
            "latency_share",
            "failed_nodes",
            "node_count",
        ]
        node_aggregate_rows = telemetry_node_aggregate(all_telemetry_rows)
        node_aggregate_fields = [
            "node",
            "total_latency_ms",
            "total_tokens",
            "total_reasoning_latency_ms",
            "total_input_size_char",
            "memory_context_used_count",
            "total_evidence_count",
            "total_trend_signal_count",
            "fallback_count",
            "fallback_indicators",
            "max_memory_write_count",
            "max_memory_skipped_count",
            "max_memory_retrieval_count",
            "max_memory_retrieval_hits_success",
            "max_memory_retrieval_hits_failure",
            "max_memory_record_count_total",
            "max_memory_record_limit",
            "max_memory_peak_record_count",
            "min_memory_remaining_capacity",
            "memory_limit_reached_count",
            "max_memory_pruned_count",
            "max_faiss_fallback_count",
            "max_faiss_recovery_count",
            "memory_backends",
            "memory_faiss_errors",
            "faiss_fallback_traces",
            "adapter_fetch_latency_ms",
            "adapter_fallback_count",
            "adapter_names",
            "source_names",
            "adapter_enabled_states",
            "adapter_fallback_reasons",
            "adapter_source_types",
            "adapter_confidences",
            "cost_per_1k_tokens_usd",
            "estimated_cost_usd",
            "token_share",
            "latency_share",
            "failed_count",
            "run_count",
        ]
        cost_gate = cost_gate_rows(telemetry_aggregate_rows, node_aggregate_rows)
        cost_gate_fields = ["metric", "actual", "warning_limit", "limit", "status"]
        write_csv(latest_dir / "regression_summary.csv", result_rows, result_fields)
        write_csv(history_dir / "regression_summary.csv", result_rows, result_fields)
        write_csv(latest_dir / "telemetry_summary.csv", all_telemetry_rows, telemetry_fields)
        write_csv(history_dir / "telemetry_summary.csv", all_telemetry_rows, telemetry_fields)
        write_csv(latest_dir / "telemetry_aggregate.csv", telemetry_aggregate_rows, telemetry_aggregate_fields)
        write_csv(history_dir / "telemetry_aggregate.csv", telemetry_aggregate_rows, telemetry_aggregate_fields)
        write_csv(latest_dir / "telemetry_node_aggregate.csv", node_aggregate_rows, node_aggregate_fields)
        write_csv(history_dir / "telemetry_node_aggregate.csv", node_aggregate_rows, node_aggregate_fields)
        write_csv(latest_dir / "cost_gate_summary.csv", cost_gate, cost_gate_fields)
        write_csv(history_dir / "cost_gate_summary.csv", cost_gate, cost_gate_fields)
        write_markdown_report(latest_dir / "regression_report.md", result_rows, warnings, telemetry_aggregate_rows, cost_gate)
        write_markdown_report(history_dir / "regression_report.md", result_rows, warnings, telemetry_aggregate_rows, cost_gate)
        if baseline_path.exists():
            shutil.copy2(baseline_path, history_dir / "baseline_compared.csv")
        for warning in warnings:
            print("WARNING", warning)
        for row in cost_gate:
            if row["status"] == "WARN":
                print(
                    "WARNING",
                    f"{row['metric']}={row['actual']} exceeded warning limit {row['warning_limit']}",
                )
        assert_cost_gate(cost_gate)
    finally:
        if server_process is not None:
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()


if __name__ == "__main__":
    main()
