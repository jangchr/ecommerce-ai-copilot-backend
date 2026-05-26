from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://ecommerce-ai-copilot-backend.onrender.com"

ENDPOINTS = {
    "sample_product": "/api/v1/generate-copilot",
    "product_description": "/api/v1/generate-from-description",
    "pasted_reviews": "/api/v1/generate-from-reviews",
}


def endpoint_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + "/" + endpoint.lstrip("/")


def post_json(url: str, payload: dict, timeout: int) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "public-demo-workflow-smoke/1.0",
            "Cache-Control": "no-cache",
        },
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
        return json.loads(body)


def response_failures(response_json: dict) -> list[str]:
    failures: list[str] = []

    if not isinstance(response_json, dict):
        return ["response is not a JSON object"]

    if "error" in response_json:
        failures.append(f"top-level error present: {response_json.get('error')}")

    if "detail" in response_json:
        failures.append(f"top-level detail present: {response_json.get('detail')}")

    data = response_json.get("data", response_json)
    if not isinstance(data, dict):
        failures.append("response data is not an object")
        return failures

    if data.get("failure_type"):
        failures.append(f"generation returned failure_type: {data.get('failure_type')}")

    blob = json.dumps(data, ensure_ascii=False).lower()

    if "hook" not in blob and "开头" not in blob:
        failures.append("missing hook marker")

    if "storyboard" not in blob and "分镜" not in blob:
        failures.append("missing storyboard marker")

    useful_terms = ["creative", "script", "scene", "strategy", "脚本", "场景", "创意"]
    if not any(term in blob for term in useful_terms):
        failures.append("missing useful generated-content terms")

    return failures


def workflow_payloads(language: str) -> dict[str, list[dict]]:
    return {
        "sample_product": [
            {
                "url": "balsamic_vinegar",
                "goal": "tiktok_ctr",
                "output_language": language,
            }
        ],
        "product_description": [
            {
                "product_name": "SoftGlow Desk Lamp",
                "product_category": "desk_lamp",
                "product_description": "A soft adjustable desk lamp for students and night workers who need comfortable lighting.",
                "customer_pain_points": "Harsh light hurts eyes, messy desk cables, and late-night work feels tiring.",
                "target_platform": "TikTok",
                "goal": "tiktok_ctr",
                "output_language": language,
            },
            {
                "product_name": "SoftGlow Desk Lamp",
                "product_category": "desk_lamp",
                "description": "A soft adjustable desk lamp for students and night workers who need comfortable lighting.",
                "pain_points": "Harsh light hurts eyes, messy desk cables, and late-night work feels tiring.",
                "target_platform": "TikTok",
                "goal": "tiktok_ctr",
                "output_language": language,
            },
        ],
        "pasted_reviews": [
            {
                "product_name": "Countertop Blender",
                "product_category": "kitchen_appliance",
                "product_description": "A compact blender for smoothies, sauces, and quick meal prep.",
                "pasted_reviews": "Great size but it is loud.\nI wish it cleaned faster.\nThe lid sometimes feels loose.\nIt blends frozen fruit well.",
                "target_platform": "TikTok",
                "goal": "tiktok_ctr",
                "output_language": language,
            },
            {
                "product_name": "Countertop Blender",
                "product_category": "kitchen_appliance",
                "product_description": "A compact blender for smoothies, sauces, and quick meal prep.",
                "reviews": [
                    "Great size but it is loud.",
                    "I wish it cleaned faster.",
                    "The lid sometimes feels loose.",
                    "It blends frozen fruit well.",
                ],
                "target_platform": "TikTok",
                "goal": "tiktok_ctr",
                "output_language": language,
            },
        ],
    }


def run_workflow(base_url: str, workflow: str, language: str, timeout: int) -> tuple[str, dict]:
    endpoint = ENDPOINTS[workflow]
    url = endpoint_url(base_url, endpoint)
    payload_candidates = workflow_payloads(language)[workflow]

    last_errors: list[str] = []

    for idx, payload in enumerate(payload_candidates, 1):
        try:
            result = post_json(url, payload, timeout)
            failures = response_failures(result)
            if failures:
                last_errors.append(f"payload candidate {idx} response failed: {'; '.join(failures)}")
                continue
            return url, result
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_errors.append(f"payload candidate {idx} HTTP {exc.code}: {body}")
            if exc.code in {400, 404, 422}:
                continue
            raise

    raise RuntimeError(f"{workflow} failed all payload candidates: " + " | ".join(last_errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test deployed public demo user workflows.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Deployed backend base URL.")
    parser.add_argument("--language", default="en", choices=["en", "zh-CN"], help="Output language.")
    parser.add_argument("--timeout", type=int, default=90, help="Request timeout per workflow in seconds.")
    parser.add_argument("--save-json", action="store_true", help="Save combined response JSON to a temp file.")
    parser.add_argument(
        "--workflow",
        choices=["all", "sample_product", "product_description", "pasted_reviews"],
        default="all",
        help="Workflow to check.",
    )
    args = parser.parse_args()

    workflows = list(ENDPOINTS.keys()) if args.workflow == "all" else [args.workflow]
    results: dict[str, dict] = {}
    failures: list[str] = []

    started_all = time.time()

    for workflow in workflows:
        print(f"\n>>> deployed workflow smoke: {workflow} ({args.language})")
        started = time.time()
        try:
            url, response_json = run_workflow(args.base_url, workflow, args.language, args.timeout)
            elapsed = time.time() - started
            results[workflow] = response_json
            print(f"PASS: {workflow} ({elapsed:.1f}s)")
            print(f"URL: {url}")
            print(f"Top-level keys: {sorted(response_json.keys())}")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            elapsed = time.time() - started
            failures.append(workflow)
            print(f"FAIL: {workflow} ({elapsed:.1f}s)")
            print(exc)

    if args.save_json:
        out = Path(tempfile.gettempdir()) / f"public_demo_workflow_smoke_{args.language}.json"
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved JSON: {out}")

    print("\n=== Public demo workflow smoke summary ===")
    print(f"Language: {args.language}")
    print(f"Workflows run: {len(workflows)}")
    print(f"Elapsed seconds: {time.time() - started_all:.1f}")

    if failures:
        print("Failed workflows:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("All public demo workflow smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
