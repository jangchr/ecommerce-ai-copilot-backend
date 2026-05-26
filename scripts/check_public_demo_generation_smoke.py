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
DEFAULT_ENDPOINT = "auto"

ENDPOINT_CANDIDATES = [
    "/generate-copilot",
    "/api/generate-copilot",
    "/api/v1/generate-copilot",
]


def endpoint_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + "/" + endpoint.lstrip("/")


def post_json(url: str, payload: dict, timeout: int) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "public-demo-generation-smoke/1.0",
            "Cache-Control": "no-cache",
        },
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
        return json.loads(body)


def post_json_with_endpoint_discovery(base_url: str, endpoint: str, payload: dict, timeout: int) -> tuple[str, dict]:
    endpoints = ENDPOINT_CANDIDATES if endpoint == "auto" else [endpoint]
    last_errors: list[str] = []

    for candidate in endpoints:
        url = endpoint_url(base_url, candidate)
        try:
            return url, post_json(url, payload, timeout)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_errors.append(f"{candidate}: HTTP {exc.code} {body}")
            if exc.code == 404:
                continue
            raise
        except json.JSONDecodeError:
            raise
        except (URLError, TimeoutError):
            raise

    raise RuntimeError("No generation endpoint candidate worked: " + " | ".join(last_errors))


def check_generation_response(response_json: dict) -> list[str]:
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

    required_terms = {
        "hook": "hook",
        "storyboard": "storyboard",
    }

    for name, term in required_terms.items():
        if term not in blob:
            failures.append(f"missing generated content marker: {name}")

    useful_terms = ["creative", "script", "scene", "feedback", "strategy", "分镜", "脚本", "开头"]
    if not any(term in blob for term in useful_terms):
        failures.append("missing useful generated-content terms")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test deployed public demo generation endpoint.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Deployed backend base URL.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Generation endpoint path, or auto.")
    parser.add_argument("--product", default="balsamic_vinegar", help="Stable local sample product slug.")
    parser.add_argument("--language", default="en", choices=["en", "zh-CN"], help="Output language.")
    parser.add_argument("--timeout", type=int, default=90, help="Request timeout in seconds.")
    parser.add_argument("--save-json", action="store_true", help="Save response JSON to a temp file.")
    args = parser.parse_args()

    payload = {
        "url": args.product,
        "goal": "tiktok_ctr",
        "output_language": args.language,
    }

    started = time.time()

    try:
        checked_url, response_json = post_json_with_endpoint_discovery(
            args.base_url,
            args.endpoint,
            payload,
            args.timeout,
        )
    except HTTPError as exc:
        print(f"Public demo generation smoke check failed: HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        return 1
    except URLError as exc:
        print(f"Public demo generation smoke check failed: URL error: {exc}")
        return 1
    except TimeoutError:
        print("Public demo generation smoke check failed: request timed out")
        return 1
    except json.JSONDecodeError as exc:
        print(f"Public demo generation smoke check failed: response was not valid JSON: {exc}")
        return 1
    except RuntimeError as exc:
        print(f"Public demo generation smoke check failed: {exc}")
        return 1

    elapsed = time.time() - started
    failures = check_generation_response(response_json)

    if args.save_json:
        out = Path(tempfile.gettempdir()) / "public_demo_generation_smoke.json"
        out.write_text(json.dumps(response_json, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved JSON: {out}")

    if failures:
        print("Public demo generation smoke check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Public demo generation smoke check passed.")
    print(f"Checked URL: {checked_url}")
    print(f"Product: {args.product}")
    print(f"Language: {args.language}")
    print(f"Elapsed seconds: {elapsed:.1f}")
    print(f"Top-level keys: {sorted(response_json.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
