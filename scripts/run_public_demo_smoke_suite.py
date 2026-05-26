from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, command: list[str]) -> int:
    print(f"\n>>> {name}")
    print(" ".join(command))

    started = time.time()
    result = subprocess.run(command, cwd=ROOT)
    elapsed = time.time() - started

    if result.returncode == 0:
        print(f"PASS: {name} ({elapsed:.1f}s)")
    else:
        print(f"FAIL: {name} ({elapsed:.1f}s)")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public demo smoke checks.")
    parser.add_argument(
        "--base-url",
        default="https://ecommerce-ai-copilot-backend.onrender.com",
        help="Deployed backend base URL.",
    )
    parser.add_argument(
        "--skip-remote",
        action="store_true",
        help="Only run local UI contract checks.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Also run frontend boundary and fast regression tests.",
    )
    parser.add_argument(
        "--include-workflows",
        action="store_true",
        help="Also run all deployed user workflow smoke checks.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run remote render smoke, generation smoke, workflow smoke, and tests.",
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Save fetched HTML / JSON artifacts to temp files.",
    )
    args = parser.parse_args()

    if args.full:
        args.include_tests = True
        args.include_workflows = True

    py = sys.executable
    failures: list[str] = []

    steps: list[tuple[str, list[str]]] = [
        (
            "local public demo UI contract",
            [py, "scripts/check_public_demo_ui_contract.py"],
        ),
    ]

    if not args.skip_remote:
        render_cmd = [
            py,
            "scripts/check_public_demo_render_smoke.py",
            "--url",
            args.base_url,
        ]
        if args.save_artifacts:
            render_cmd.append("--save-html")

        generation_en_cmd = [
            py,
            "scripts/check_public_demo_generation_smoke.py",
            "--base-url",
            args.base_url,
            "--language",
            "en",
            "--product",
            "balsamic_vinegar",
        ]
        generation_zh_cmd = [
            py,
            "scripts/check_public_demo_generation_smoke.py",
            "--base-url",
            args.base_url,
            "--language",
            "zh-CN",
            "--product",
            "desk_lamp",
        ]

        if args.save_artifacts:
            generation_en_cmd.append("--save-json")
            generation_zh_cmd.append("--save-json")

        steps.extend(
            [
                ("deployed render HTML smoke", render_cmd),
                ("deployed generation smoke EN", generation_en_cmd),
                ("deployed generation smoke zh-CN", generation_zh_cmd),
            ]
        )

        if args.include_workflows:
            workflow_en_cmd = [
                py,
                "scripts/check_public_demo_workflow_smoke.py",
                "--base-url",
                args.base_url,
                "--language",
                "en",
            ]
            workflow_zh_cmd = [
                py,
                "scripts/check_public_demo_workflow_smoke.py",
                "--base-url",
                args.base_url,
                "--language",
                "zh-CN",
            ]

            if args.save_artifacts:
                workflow_en_cmd.append("--save-json")
                workflow_zh_cmd.append("--save-json")

            steps.extend(
                [
                    ("deployed workflow smoke EN", workflow_en_cmd),
                    ("deployed workflow smoke zh-CN", workflow_zh_cmd),
                ]
            )

    if args.include_tests:
        steps.extend(
            [
                (
                    "frontend boundary tests",
                    [py, "-m", "unittest", "tests.test_frontend_probe_boundary"],
                ),
                (
                    "fast regression tests",
                    [py, "scripts/run_all_tests.py", "--fast"],
                ),
            ]
        )

    started_all = time.time()

    for name, command in steps:
        code = run_step(name, command)
        if code != 0:
            failures.append(name)

    elapsed_all = time.time() - started_all

    print("\n=== Public demo smoke suite summary ===")
    print(f"Steps run: {len(steps)}")
    print(f"Elapsed seconds: {elapsed_all:.1f}")

    if failures:
        print("Failed steps:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("All public demo smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
