import importlib
import json
import os
import platform
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REVIEW_DATASETS = [
    "balsamic_vinegar.json",
    "printer.json",
    "women_bras.json",
    "girls_overalls.json",
    "protein_powder.json",
    "phone_case.json",
    "desk_lamp.json",
    "baby_stroller.json",
    "pet_hair_vacuum.json",
    "skincare_serum.json",
]


def import_status(module_name: str) -> dict:
    try:
        module = importlib.import_module(module_name)
        return {
            "ok": True,
            "version": getattr(module, "__version__", ""),
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "version": "",
            "error": str(exc),
        }


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    dataset_dir = PROJECT_ROOT / "data" / "reviews"
    dataset_status = {
        name: (dataset_dir / name).exists() for name in EXPECTED_REVIEW_DATASETS
    }
    dependencies = {
        "faiss": import_status("faiss"),
        "sentence_transformers": import_status("sentence_transformers"),
        "langchain_huggingface": import_status("langchain_huggingface"),
    }
    baselines = {
        "l9_3_phase_2d": (PROJECT_ROOT / "runs" / "baselines" / "l9_3_phase_2d").exists(),
        "l9_6_f_faiss_recovery": (
            PROJECT_ROOT / "runs" / "baselines" / "l9_6_f_faiss_recovery"
        ).exists(),
    }
    project_files = {
        "requirements_lock": (PROJECT_ROOT / "requirements.lock.txt").exists(),
        "env_example": (PROJECT_ROOT / ".env.example").exists(),
    }
    required_failures = []
    if not os.getenv("OPENAI_API_KEY"):
        required_failures.append("OPENAI_API_KEY missing")
    if not dependencies["faiss"]["ok"]:
        required_failures.append("faiss import failed")
    if not dependencies["sentence_transformers"]["ok"]:
        required_failures.append("sentence_transformers import failed")
    required_failures.extend(
        f"data/reviews/{name} missing"
        for name, exists in dataset_status.items()
        if not exists
    )
    if not baselines["l9_3_phase_2d"]:
        required_failures.append("runs/baselines/l9_3_phase_2d missing")
    if not baselines["l9_6_f_faiss_recovery"]:
        required_failures.append("runs/baselines/l9_6_f_faiss_recovery missing")
    if not project_files["requirements_lock"]:
        required_failures.append("requirements.lock.txt missing")
    if not project_files["env_example"]:
        required_failures.append(".env.example missing")

    result = {
        "status": "fail" if required_failures else "pass",
        "required_failures": required_failures,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "llm_config": {
            "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
            "openai_api_base": os.getenv("OPENAI_API_BASE", ""),
            "model_name": os.getenv("MODEL_NAME", ""),
        },
        "dependencies": dependencies,
        "review_datasets": {
            "directory": str(dataset_dir),
            "expected_count": len(EXPECTED_REVIEW_DATASETS),
            "all_present": all(dataset_status.values()),
            "files": dataset_status,
        },
        "baselines": baselines,
        "project_files": project_files,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if required_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
