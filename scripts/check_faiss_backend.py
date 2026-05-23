import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.workflow import FaissMemoryEngine


def main() -> None:
    engine = FaissMemoryEngine()
    faiss_ok = engine._ensure_faiss(operation="manual_check")
    snapshot = engine.observability_snapshot()
    faiss = snapshot.get("faiss_observability", {})
    result = {
        "faiss_ok": faiss_ok,
        "backend": snapshot.get("backend", ""),
        "faiss_error": snapshot.get("faiss_error", ""),
        "fallback_count": faiss.get("fallback_count", 0),
        "recovery_count": faiss.get("recovery_count", 0),
        "fallback_trace": faiss.get("fallback_trace", []),
        "memory_record_count": snapshot.get("memory_record_count", {}),
        "memory_growth": snapshot.get("memory_growth", {}),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
