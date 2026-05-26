from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "static" / "index.html"


REQUIRED_MARKERS = {
    "L24 marker": "// L24-B copy-ready script extraction from structured model output",
    "structured prefix stripper": "function stripStructuredScriptPrefix(text)",
    "clean hook helper": "function cleanHookLine(script)",
    "clean cta helper": "function cleanCtaLine(script)",
    "copy-ready builder": "function copyReadyScriptText(data)",
    "narration extraction": "Narration|旁白",
    "visual line output": "Visual: ${visual}",
    "Chinese visual line output": "画面：${visual}",
    "narration line output": "Narration: ${narration}",
    "Chinese narration line output": "旁白：${narration}",
    "data-aware quick use signature": "function renderQuickUsePack(script, storyboard, data = null)",
    "data-aware quick use call": "renderQuickUsePack(script, storyboard, data)",
    "quick use render slot": "${quickUsePackCard}",
    "copy-ready assignment": "const copyReady = copyReadyScriptText(fallbackData);",
    "quick use copy source": "latestQuickUseScript = copyReady;",
    "clean hook highlight": "const hook = cleanHookLine(script);",
    "clean cta highlight": "const cta = cleanCtaLine(script);",
    "clean hook copy action": "const hook = cleanHookLine(latestProductData?.assets?.tiktok_script || {});",
}


FORBIDDEN_PATTERNS = {
    "raw hook highlight": "escapeHTML(script.hook || '')",
    "raw cta highlight": "escapeHTML(script.cta || '')",
    "raw quick-use hook copy": "latestQuickUseScript = script.hook",
    "old quick-use signature assertion target": "function renderQuickUsePack(script, storyboard) {",
}


def section_between(source: str, start_marker: str, end_marker: str) -> str:
    start = source.find(start_marker)
    if start == -1:
        return ""
    end = source.find(end_marker, start + len(start_marker))
    if end == -1:
        return source[start:]
    return source[start:end]


def check_source(source: str) -> list[str]:
    failures: list[str] = []

    for name, marker in REQUIRED_MARKERS.items():
        if marker not in source:
            failures.append(f"missing marker: {name} -> {marker}")

    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern in source:
            failures.append(f"forbidden raw/internal pattern: {name} -> {pattern}")

    dashboard = section_between(
        source,
        "function renderProductDashboard(data, options = {}) {",
        "function renderDebugPanel",
    )

    if not dashboard:
        failures.append("could not isolate renderProductDashboard section")
    else:
        if dashboard.count("renderQuickUsePack(script, storyboard, data)") != 1:
            failures.append("renderProductDashboard should call renderQuickUsePack(script, storyboard, data) exactly once")
        if dashboard.count("${quickUsePackCard}") != 1:
            failures.append("renderProductDashboard should render ${quickUsePackCard} exactly once")
        if dashboard.find("${hookHighlightCard}") > dashboard.find("${quickUsePackCard}"):
            failures.append("hookHighlightCard should appear before quickUsePackCard")

    hook_card = section_between(
        source,
        "function renderHookHighlightCard(script) {",
        "function resultSummaryTitle",
    )

    if hook_card:
        if "script.hook" in hook_card or "script.cta" in hook_card:
            failures.append("renderHookHighlightCard should not render raw script.hook or script.cta directly")

    return failures


def main() -> int:
    source = INDEX.read_text(encoding="utf-8")
    failures = check_source(source)

    if failures:
        print("Copy-ready script contract check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Copy-ready script contract check passed.")
    print(f"Checked: {INDEX}")
    print(f"Required markers: {len(REQUIRED_MARKERS)}")
    print(f"Forbidden patterns: {len(FORBIDDEN_PATTERNS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
