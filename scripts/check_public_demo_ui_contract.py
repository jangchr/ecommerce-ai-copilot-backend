from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "static" / "index.html"

source = HTML.read_text(encoding="utf-8")

checks = {
    "L21-A workflow entry hierarchy": "/* L21-A primary workflow entry hierarchy */",
    "L21-B result-first hierarchy": "/* L21-B result-first content hierarchy */",
    "L21-C diagnostics secondary": "/* L21-C keep technical diagnostics secondary */",
    "L21-D copy action hierarchy": "/* L21-D make copy actions the next obvious step */",
    "L21-E language body classes": "function updateLanguageBodyClass(language)",
    "L21-F actionable empty state": "/* L21-F actionable empty result state */",
    "sample workspace language map": "const SAMPLE_WORKSPACE_COPY",
    "zh body copy mode": "body.zh-mode",
    "en body copy mode": "en-mode",
    "localized sample slug normalization": "function sampleWorkspaceSlugFromValue(value)",
    "sample request sends normalized slug": "const payload = { url: urlInput, goal: 'tiktok_ctr', output_language: currentOutputLanguage() };",
    "English copy action hint": 'content: "Next: copy what you need";',
    "Chinese copy action hint": 'content: "下一步：复制你要用的内容";',
    "English empty state hint": 'content: "Pick a path above, add a product idea or sample, then generate.";',
    "Chinese empty state hint": 'content: "先选择上面的入口，填写产品或选择示例，然后点击生成。";',
    "Chinese balsamic display": '"balsamic_vinegar": "香醋"',
    "English balsamic display": '"balsamic_vinegar": "balsamic_vinegar"',
}

forbidden = {
    "garbled question marks": "????",
    "mixed balsamic display": "香醋 / balsamic_vinegar",
    "mixed desk lamp display": "台灯 / desk_lamp",
    "mixed pet hair display": "宠物毛发清理 / pet_hair_vacuum",
}

failed = []

for name, needle in checks.items():
    if needle not in source:
        failed.append(f"missing: {name} -> {needle}")

for name, needle in forbidden.items():
    if needle in source:
        failed.append(f"forbidden: {name} -> {needle}")

if failed:
    print("Public demo UI contract check failed:")
    for item in failed:
        print(f"- {item}")
    sys.exit(1)

print("Public demo UI contract check passed.")
print(f"Checked: {HTML}")
print(f"Required markers: {len(checks)}")
print(f"Forbidden patterns: {len(forbidden)}")
