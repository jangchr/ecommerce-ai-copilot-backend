import os


DEFAULT_ENABLED_TOOLS = ["local_review_dataset", "tiktok_trend_mock"]
REAL_SOURCE_TOOLS = ["amazon_review_api", "tiktok_trend_api", "reddit_review_api"]


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


ALLOW_REAL_SOURCE_ADAPTERS = _env_flag("ALLOW_REAL_SOURCE_ADAPTERS", default=False)


def enabled_source_tools() -> list[str]:
    if not ALLOW_REAL_SOURCE_ADAPTERS:
        return list(DEFAULT_ENABLED_TOOLS)
    # These tools are only exposed behind the explicit flag. Their adapters remain
    # unavailable shells until provider-specific implementations are added.
    return [*DEFAULT_ENABLED_TOOLS, *REAL_SOURCE_TOOLS]
