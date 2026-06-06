import os
import subprocess
import sys

from dotenv import load_dotenv


FAST_COMMANDS = [
    [sys.executable, "-m", "compileall", "main.py", "agent_runs.py", "agent_graph_storage.py", "core", "schemas", "source_adapters", "scripts", "tests"],
    [
        sys.executable,
        "-m",
        "unittest",
        "tests.test_reward_engine",
        "tests.test_memory_bucket",
        "tests.test_source_adapters",
        "tests.test_amazon_probe_adapter",
        "tests.test_amazon_external_crawler_contract",
        "tests.test_apify_amazon_crawler_worker",
        "tests.test_local_playwright_amazon_crawler_worker",
        "tests.test_amazon_intake_endpoint",
        "tests.test_review_workspace_endpoint",
        "tests.test_review_paste_parser_endpoint",
        "tests.test_pasted_review_workspace_endpoint",
        "tests.test_amazon_shadow_eval_runner",
        "tests.test_source_registry",
        "tests.test_runtime_config",
        "tests.test_strategy_node",
        "tests.test_cognitive_synthesis",
        "tests.test_regression_diff_gate",
        "tests.test_api_contract",
        "tests.test_shadow_mode_contract",
        "tests.test_api_live_smoke",
        "tests.test_product_description_endpoint",
        "tests.test_language_mode_backend",
        "tests.test_pasted_reviews_endpoint",
        "tests.test_project_sources",
        "tests.test_agent_runs",
        "tests.test_agent_graph_storage",
        "tests.test_video_generation_jobs",
        "tests.test_translation_endpoint",
        "tests.test_source_probe_contract",
        "tests.test_source_probe_endpoint",
        "tests.test_frontend_probe_boundary",
        "tests.test_browser_extension_contract",
        "tests.test_health_endpoint",
        "tests.test_startup_preflight",
        "tests.test_request_id_logging",
        "tests.test_telemetry_utils",
    ],
    [sys.executable, "scripts/run_failure_tests.py"],
    [sys.executable, "scripts/run_route_failure_tests.py"],
]

FULL_COMMANDS = FAST_COMMANDS + [
    [sys.executable, "scripts/run_debug_tests.py"],
]


def main():
    load_dotenv()
    fast = "--fast" in sys.argv
    if not fast and not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing; full LLM regression cannot run.")
        raise SystemExit(1)

    commands = FAST_COMMANDS if fast else FULL_COMMANDS

    for command in commands:
        print("\n>>>", " ".join(command), flush=True)
        result = subprocess.run(command)
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    mode = "fast" if fast else "full"
    print(f"\nAll L9 {mode} regression tests passed.")


if __name__ == "__main__":
    main()
