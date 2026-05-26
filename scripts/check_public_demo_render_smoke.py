from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_URL = "https://ecommerce-ai-copilot-backend.onrender.com/"


REQUIRED_MARKERS = {
    "L21-A workflow entry hierarchy": "L21-A",
    "L21-B result-first hierarchy": "L21-B",
    "L21-C diagnostics secondary": "L21-C",
    "L21-D copy action hierarchy": "L21-D",
    "L21-E language body classes": "L21-E",
    "L21-F actionable empty state": "L21-F",
    "sample workspace language map": "SAMPLE_WORKSPACE_COPY",
    "language class helper": "updateLanguageBodyClass",
    "zh body class": "zh-mode",
    "English copy hint": "Next: copy what you need",
    "Chinese empty state hint": "先选择上面的入口",
}


FORBIDDEN_PATTERNS = {
    "garbled question marks": "????",
    "mixed balsamic display": "香醋 / balsamic_vinegar",
    "mixed desk lamp display": "台灯 / desk_lamp",
    "mixed pet hair display": "宠物毛发清理 / pet_hair_vacuum",
    "old inline panel fallback": "Inline Result Panel",
}


def fetch_html(url: str, timeout: int) -> str:
    cache_buster = f"render-smoke-{int(time.time())}"
    sep = "&" if "?" in url else "?"
    smoke_url = f"{url}{sep}v={cache_buster}"

    request = Request(
        smoke_url,
        headers={
            "User-Agent": "public-demo-render-smoke/1.0",
            "Cache-Control": "no-cache",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def check_html(html: str) -> list[str]:
    failures: list[str] = []

    for name, marker in REQUIRED_MARKERS.items():
        if marker not in html:
            failures.append(f"missing marker: {name} -> {marker}")

    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern in html:
            failures.append(f"forbidden pattern: {name} -> {pattern}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Check deployed public demo UI smoke markers.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Public demo URL to check.")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds.")
    parser.add_argument("--save-html", action="store_true", help="Save fetched HTML to a temp file.")
    args = parser.parse_args()

    html = fetch_html(args.url, args.timeout)
    failures = check_html(html)

    if args.save_html:
        out = Path(tempfile.gettempdir()) / "public_demo_render_smoke.html"
        out.write_text(html, encoding="utf-8")
        print(f"Saved HTML: {out}")

    if failures:
        print("Public demo Render smoke check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Public demo Render smoke check passed.")
    print(f"Checked URL: {args.url}")
    print(f"Required markers: {len(REQUIRED_MARKERS)}")
    print(f"Forbidden patterns: {len(FORBIDDEN_PATTERNS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
