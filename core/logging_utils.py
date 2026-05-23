import json
from typing import Any, Optional


SAFE_EVENT_FIELDS = {
    "endpoint",
    "status",
    "latency_ms",
    "product_category",
    "goal",
    "provider_count",
    "fallback_required",
}


def emit_event(event: str, request_id: Optional[str], **fields: Any) -> None:
    payload = {
        "event": event,
        "request_id": request_id,
    }
    payload.update(
        {
            key: value
            for key, value in fields.items()
            if key in SAFE_EVENT_FIELDS and value is not None
        }
    )
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")), flush=True)
