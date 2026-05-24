import argparse
import csv
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


BASE_URL = "http://127.0.0.1:8001"
OUTPUT_ROOT = Path("runs/amazon_shadow_eval")
DEBUG_ENDPOINT = "/api/v1/debug-copilot"
PROBE_ENDPOINT = "/api/v1/debug-source-probe"
PRODUCT_ENDPOINT = "/api/v1/generate-copilot"

EVALUATION_URLS = [
    {
        "category": "balsamic_vinegar",
        "url": "https://www.amazon.com/dp/B00QIIMCCW",
    },
    {
        "category": "printer",
        "url": "https://us.amazon.com/Epson-WF-C5790-Printer-Scanner-Copier/dp/B079HWMZTZ",
    },
    {
        "category": "women_bras",
        "url": "https://us.amazon.com/Triumph-Minimizer-Sensation-Seamless-Lingerie/dp/B08F1T13GV",
    },
    {
        "category": "women_bras",
        "url": "https://us.amazon.com/Smart-Sexy-Cleavage-Underwire-Available/dp/B0DHGRYG59",
    },
    {
        "category": "protein_powder",
        "url": "https://us.amazon.com/Asitis-Nutrition-Whey-Protein-Concentrate/dp/B083DXW553",
    },
    {
        "category": "protein_powder",
        "url": "https://us.amazon.com/Max-Titanium-Concentrate-Hydrolyzed-Recovery/dp/B07ZBGBCGD",
    },
    {
        "category": "phone_case",
        "url": "https://www.amazon.com/Spigen-Liquid-Designed-Moto-Stylus/dp/B0D6X6GZ8Y",
    },
    {
        "category": "phone_case",
        "url": "https://www.amazon.com/OtterBox-iPhone-Symmetry-Clear-Case/dp/B0FJPWPDD2",
    },
    {
        "category": "desk_lamp",
        "url": "https://us.amazon.com/DEWENWILS-Minimalist-Dimmable-Lighting-Standing/dp/B092V42HPT",
    },
    {
        "category": "desk_lamp",
        "url": "https://us.amazon.com/Amazon-Basics-Adjustable-Laptop-Table/dp/B09MHB5ZXL",
    },
    {
        "category": "baby_stroller",
        "url": "https://us.amazon.com/Inglesina-Aptica-Stroller-Indigo-Denim/dp/B07GRJSM4Z",
    },
    {
        "category": "baby_stroller",
        "url": "https://us.amazon.com/Joolz-Day-Stroller-One-Hand-Comfortable/dp/B0968R16DQ",
    },
    {
        "category": "baby_stroller",
        "url": "https://us.amazon.com/Evenflo-Modular-Travel-LiteMax-Rear-Facing/dp/B0CLYS8T9Z",
    },
    {
        "category": "pet_hair_vacuum",
        "url": "https://www.amazon.com/dp/B001EYFQ28",
    },
    {
        "category": "pet_hair_vacuum",
        "url": "https://www.amazon.com/dp/B07CB6RBSP",
    },
    {
        "category": "pet_hair_vacuum",
        "url": "https://www.amazon.com/dp/B083JWGWK2",
    },
    {
        "category": "skincare_serum",
        "url": "https://us.amazon.com/Lulu-Organics-Botanical-Face-Serum/dp/B07KTG4JVD",
    },
    {
        "category": "skincare_serum",
        "url": "https://us.amazon.com/APLB-Skincare-elasticity-Sensitive-Revitalize/dp/B0DG8N398L",
    },
    {
        "category": "skincare_serum",
        "url": "https://us.amazon.com/Revox-B77-Alpha-Arbutin-Brightening/dp/B09FK48BYR",
    },
    {
        "category": "skincare_serum",
        "url": "https://us.amazon.com/CeraVe-Facial-Moisturizing-Lotion-Cerave/dp/B018MR63HG",
    },
]

CSV_FIELDS = [
    "url",
    "category",
    "provider_status",
    "source_confidence",
    "product_title_present",
    "rating_present",
    "review_count_present",
    "evidence_preview_count",
    "bullet_points_count",
    "category_hint_present",
    "latency_ms",
    "fallback_required",
    "memory_write_allowed",
    "used_for_generation",
    "error_type",
    "notes",
]


def post_debug_copilot(base_url: str, item: dict[str, str], timeout: int = 180) -> dict[str, Any]:
    body = json.dumps(
        {
            "url": item["url"],
            "goal": "tiktok_ctr",
            "real_source_mode": "amazon_shadow",
        }
    ).encode("utf-8")
    req = urllib_request.Request(
        f"{base_url.rstrip('/')}{DEBUG_ENDPOINT}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_debug_source_probe(base_url: str, item: dict[str, str], timeout: int = 180) -> dict[str, Any]:
    body = json.dumps(
        {
            "product_category": item["category"],
            "url": item["url"],
            "providers": ["amazon_review_api"],
            "debug_only": True,
        }
    ).encode("utf-8")
    req = urllib_request.Request(
        f"{base_url.rstrip('/')}{PROBE_ENDPOINT}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fallback_required(provider_status: str, source_confidence: float) -> bool:
    return not (provider_status == "success" and source_confidence >= 0.70)


def error_type_from(status: str, error: str) -> str:
    if status == "success" and not error:
        return ""
    if status in {"disabled", "unavailable", "error"}:
        return status
    return "unknown"


def row_from_response(item: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    shadow = payload.get("shadow_sources") or {}
    amazon = shadow.get("amazon_review_api") or {}
    metadata = amazon.get("metadata") or {}
    evidence_preview = amazon.get("evidence_preview") or []
    bullet_points = metadata.get("bullet_points") or []
    status = amazon.get("status") or "missing"
    confidence = float(amazon.get("source_confidence") or 0.0)
    memory_write_allowed = bool(shadow.get("memory_write_allowed", True))
    used_for_generation = bool(shadow.get("used_for_generation", True))
    notes = []
    if memory_write_allowed:
        notes.append("FAIL: memory_write_allowed must be false")
    if used_for_generation:
        notes.append("FAIL: used_for_generation must be false")

    return {
        "url": item["url"],
        "category": item["category"],
        "provider_status": status,
        "source_confidence": confidence,
        "product_title_present": bool(metadata.get("product_title")),
        "rating_present": bool(metadata.get("rating")),
        "review_count_present": bool(metadata.get("review_count")),
        "evidence_preview_count": len(evidence_preview),
        "bullet_points_count": len(bullet_points),
        "category_hint_present": bool(metadata.get("category_hint") or metadata.get("product_category_hint")),
        "latency_ms": float(amazon.get("latency_ms") or 0.0),
        "fallback_required": fallback_required(status, confidence),
        "memory_write_allowed": memory_write_allowed,
        "used_for_generation": used_for_generation,
        "error_type": "safety_fail" if notes else error_type_from(status, amazon.get("error", "")),
        "notes": "; ".join(notes) or amazon.get("error", ""),
    }


def row_from_probe_response(item: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results") or []
    amazon = next(
        (result for result in results if result.get("provider") == "amazon_review_api"),
        {},
    )
    metadata = amazon.get("metadata") or {}
    evidence_preview = amazon.get("evidence_preview") or []
    bullet_points = metadata.get("bullet_points") or []
    status = amazon.get("status") or "missing"
    confidence = float(amazon.get("source_confidence") or 0.0)
    memory_write_allowed = bool(payload.get("memory_write_allowed", True))
    used_for_generation = False
    notes = []
    if memory_write_allowed:
        notes.append("FAIL: memory_write_allowed must be false")

    return {
        "url": item["url"],
        "category": item["category"],
        "provider_status": status,
        "source_confidence": confidence,
        "product_title_present": bool(metadata.get("product_title")),
        "rating_present": bool(metadata.get("rating")),
        "review_count_present": bool(metadata.get("review_count")),
        "evidence_preview_count": len(evidence_preview),
        "bullet_points_count": len(bullet_points),
        "category_hint_present": bool(metadata.get("category_hint") or metadata.get("product_category_hint")),
        "latency_ms": float(amazon.get("latency_ms") or 0.0),
        "fallback_required": bool(payload.get("fallback_required", fallback_required(status, confidence))),
        "memory_write_allowed": memory_write_allowed,
        "used_for_generation": used_for_generation,
        "error_type": "safety_fail" if notes else error_type_from(status, amazon.get("error", "")),
        "notes": "; ".join(notes) or amazon.get("error", ""),
    }


def row_from_exception(item: dict[str, str], exc: Exception) -> dict[str, Any]:
    if isinstance(exc, HTTPError):
        error = f"http_{exc.code}"
    elif isinstance(exc, URLError):
        error = "url_error"
    else:
        error = exc.__class__.__name__
    return {
        "url": item["url"],
        "category": item["category"],
        "provider_status": "error",
        "source_confidence": 0.0,
        "product_title_present": False,
        "rating_present": False,
        "review_count_present": False,
        "evidence_preview_count": 0,
        "bullet_points_count": 0,
        "category_hint_present": False,
        "latency_ms": 0.0,
        "fallback_required": True,
        "memory_write_allowed": False,
        "used_for_generation": False,
        "error_type": error,
        "notes": str(exc),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


def summarize_rows(
    rows: list[dict[str, Any]],
    probe_only: bool = False,
) -> dict[str, Any]:
    total = len(rows)
    statuses = {status: 0 for status in ["success", "disabled", "unavailable", "error", "missing"]}
    for row in rows:
        statuses[row["provider_status"]] = statuses.get(row["provider_status"], 0) + 1

    confidences = [float(row["source_confidence"]) for row in rows if row["provider_status"] == "success"]
    latencies = [float(row["latency_ms"]) for row in rows]
    preview_non_empty = sum(int(row["evidence_preview_count"]) > 0 for row in rows)
    metadata_fields = [
        "product_title_present",
        "rating_present",
        "review_count_present",
        "category_hint_present",
    ]
    metadata_counts = {
        field: sum(bool(row[field]) for row in rows)
        for field in metadata_fields
    }
    safety_failures = [
        row for row in rows
        if row["memory_write_allowed"] or row["used_for_generation"] or row["error_type"] == "safety_fail"
    ]

    return {
        "total": total,
        "status_counts": statuses,
        "average_source_confidence": round(statistics.mean(confidences), 4) if confidences else 0.0,
        "evidence_preview_non_empty_rate": round(preview_non_empty / total, 4) if total else 0.0,
        "metadata_completeness": {
            field: round(count / total, 4) if total else 0.0
            for field, count in metadata_counts.items()
        },
        "p50_latency_ms": round(percentile(latencies, 50), 2),
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "safety_failure_count": len(safety_failures),
        "product_api_called": False,
        "debug_copilot_called": not probe_only,
        "probe_only": probe_only,
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, Any]], summary: dict[str, Any], path: Path) -> None:
    failed = [row for row in rows if row["provider_status"] in {"error", "unavailable", "missing"}]
    metadata = summary["metadata_completeness"]
    lines = [
        "# Amazon Shadow Evaluation Report",
        "",
        "This report is produced by `scripts/run_amazon_shadow_eval.py` and is not part of fast or full regression gates.",
        "",
        "## Summary",
        "",
        f"- Total URLs: {summary['total']}",
        f"- Success count: {summary['status_counts'].get('success', 0)}",
        f"- Unavailable count: {summary['status_counts'].get('unavailable', 0)}",
        f"- Error count: {summary['status_counts'].get('error', 0)}",
        f"- Average source_confidence: {summary['average_source_confidence']}",
        f"- Evidence preview non-empty rate: {summary['evidence_preview_non_empty_rate']}",
        f"- p50 latency_ms: {summary['p50_latency_ms']}",
        f"- p95 latency_ms: {summary['p95_latency_ms']}",
        f"- Safety failure count: {summary['safety_failure_count']}",
        f"- Product API called: {str(summary['product_api_called']).lower()}",
        f"- Debug Copilot called: {str(summary['debug_copilot_called']).lower()}",
        f"- Probe-only mode: {str(summary['probe_only']).lower()}",
        "",
        "## Metadata Completeness",
        "",
        f"- product_title_present: {metadata['product_title_present']}",
        f"- rating_present: {metadata['rating_present']}",
        f"- review_count_present: {metadata['review_count_present']}",
        f"- category_hint_present: {metadata['category_hint_present']}",
        "",
        "## Safety Statement",
        "",
        "- memory_write_allowed must remain false for every row.",
        "- used_for_generation must remain false for every row.",
        "- The runner never calls `/api/v1/generate-copilot`.",
        "- In probe-only mode, the runner calls `/api/v1/debug-source-probe` and does not call `/api/v1/debug-copilot`.",
        "- Amazon shadow evidence is not used for generation and must not write memory.",
        "",
        "## Failed Or Unavailable URLs",
        "",
    ]
    if failed:
        for row in failed:
            lines.append(f"- `{row['provider_status']}` `{row['category']}` {row['url']} :: {row['error_type']} {row['notes']}")
    else:
        lines.append("- None")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_evaluation(
    items: list[dict[str, str]] | None = None,
    base_url: str = BASE_URL,
    output_root: Path = OUTPUT_ROOT,
    probe_only: bool = False,
) -> Path:
    items = items or EVALUATION_URLS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_root / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in items:
        try:
            if probe_only:
                payload = post_debug_source_probe(base_url, item)
                rows.append(row_from_probe_response(item, payload))
            else:
                payload = post_debug_copilot(base_url, item)
                rows.append(row_from_response(item, payload))
        except Exception as exc:
            rows.append(row_from_exception(item, exc))

    summary = summarize_rows(rows, probe_only=probe_only)
    write_csv(rows, output_dir / "amazon_shadow_eval_summary.csv")
    write_report(rows, summary, output_dir / "amazon_shadow_eval_report.md")
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run manual Amazon shadow evaluation against a local backend."
    )
    parser.add_argument(
        "--probe-only",
        action="store_true",
        help="Call /api/v1/debug-source-probe instead of /api/v1/debug-copilot.",
    )
    args = parser.parse_args()

    output_dir = run_evaluation(probe_only=args.probe_only)
    print(f"Amazon shadow evaluation written to {output_dir}")
    if args.probe_only:
        print("Probe-only mode: debug-source-probe called, debug-copilot skipped.")
    else:
        print("End-to-end shadow mode: debug-copilot called.")
    print("This manual runner does not call the product API and does not write memory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
