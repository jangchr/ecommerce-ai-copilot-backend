import importlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Mapping, Optional

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIN_REVIEW_DATASET_COUNT = 10
STABLE_BASELINE_PATH = Path("runs") / "baselines" / "l9_9_stable"
REQUIRED_PROJECT_FILES = [
    Path("main.py"),
    Path("core") / "workflow.py",
    Path("schemas") / "api_contract.py",
    Path("source_adapters") / "registry.py",
    Path("requirements.txt"),
    Path(".env.example"),
]


def optional_import_status(module_name: str) -> dict:
    try:
        module = importlib.import_module(module_name)
        return {
            "available": True,
            "version": getattr(module, "__version__", ""),
            "error": "",
        }
    except Exception as exc:
        return {
            "available": False,
            "version": "",
            "error": str(exc),
        }


def parse_positive_int(raw: str, name: str, failures: list[str]) -> Optional[int]:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        failures.append(f"{name} must be a positive integer")
        return None
    if value <= 0:
        failures.append(f"{name} must be a positive integer")
        return None
    return value


def collect_startup_preflight(
    project_root: Path = PROJECT_ROOT,
    environment: Optional[Mapping[str, str]] = None,
) -> dict:
    env = environment if environment is not None else os.environ
    required_failures: list[str] = []

    project_files = {
        str(relative).replace("\\", "/"): (project_root / relative).exists()
        for relative in REQUIRED_PROJECT_FILES
    }
    review_dir = project_root / "data" / "reviews"
    review_files = sorted(path.name for path in review_dir.glob("*.json")) if review_dir.exists() else []
    baseline_exists = (project_root / STABLE_BASELINE_PATH).exists()

    if not review_dir.exists():
        required_failures.append("data/reviews missing")
    elif len(review_files) < MIN_REVIEW_DATASET_COUNT:
        required_failures.append(
            f"data/reviews dataset count below {MIN_REVIEW_DATASET_COUNT}"
        )
    if not baseline_exists:
        required_failures.append("runs/baselines/l9_9_stable missing")
    if not project_files["requirements.txt"]:
        required_failures.append("requirements.txt missing")
    if not project_files[".env.example"]:
        required_failures.append(".env.example missing")

    memory_limit_raw = env.get("MEMORY_MAX_RECORD_COUNT", "500")
    memory_limit = parse_positive_int(
        memory_limit_raw,
        "MEMORY_MAX_RECORD_COUNT",
        required_failures,
    )
    allow_real_sources = env.get("ALLOW_REAL_SOURCE_ADAPTERS", "false").strip().lower()

    checks = {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "project_files": project_files,
        "review_datasets": {
            "directory": str(review_dir),
            "exists": review_dir.exists(),
            "minimum_count": MIN_REVIEW_DATASET_COUNT,
            "count": len(review_files),
            "files": review_files,
        },
        "stable_baseline": {
            "path": str(STABLE_BASELINE_PATH).replace("\\", "/"),
            "exists": baseline_exists,
        },
        "runtime_config": {
            "openai_api_key_present": bool(env.get("OPENAI_API_KEY")),
            "allow_real_source_adapters": allow_real_sources,
            "safe_default_sources": allow_real_sources == "false",
            "memory_max_record_count_raw": memory_limit_raw,
            "memory_max_record_count": memory_limit,
        },
        "optional_dependencies": {
            "faiss": optional_import_status("faiss"),
        },
    }
    return {
        "status": "fail" if required_failures else "pass",
        "required_failures": required_failures,
        "checks": checks,
    }


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    result = collect_startup_preflight()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["required_failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
