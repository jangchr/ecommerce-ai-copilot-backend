from dataclasses import dataclass
import time
from typing import Dict

from schemas.source_contract import SourceEvidence
from source_adapters.amazon_review_adapter import AmazonReviewAdapter
from source_adapters.base import BaseSourceAdapter
from source_adapters.local_review_adapter import LocalReviewAdapter
from source_adapters.mock_trend_adapter import MockTrendAdapter
from source_adapters.reddit_review_adapter import RedditReviewAdapter
from source_adapters.tiktok_trend_adapter import TikTokTrendAdapter


@dataclass(frozen=True)
class AdapterRegistration:
    adapter: BaseSourceAdapter
    enabled: bool


class SourceAdapterRegistry:
    def __init__(self):
        self._registrations: Dict[str, AdapterRegistration] = {}
        self.register("local_review_dataset", LocalReviewAdapter(), enabled=True)
        self.register("tiktok_trend_mock", MockTrendAdapter(), enabled=True)
        self.register("amazon_review_api", AmazonReviewAdapter(), enabled=False)
        self.register("tiktok_trend_api", TikTokTrendAdapter(), enabled=False)
        self.register("reddit_review_api", RedditReviewAdapter(), enabled=False)

    def register(self, name: str, adapter: BaseSourceAdapter, enabled: bool) -> None:
        self._registrations[name] = AdapterRegistration(adapter=adapter, enabled=enabled)

    def get(self, name: str) -> BaseSourceAdapter:
        try:
            return self._registrations[name].adapter
        except KeyError as exc:
            raise ValueError(f"Unknown source adapter: {name}") from exc

    def is_enabled(self, name: str) -> bool:
        return name in self._registrations and self._registrations[name].enabled

    def adapter_name(self, name: str) -> str:
        return self.get(name).__class__.__name__

    def enabled_tools(self) -> list[str]:
        return [name for name, item in self._registrations.items() if item.enabled]

    def fetch(self, name: str, url: str, product_category: str) -> SourceEvidence:
        return self.get(name).fetch(url, product_category)

    def fetch_with_trace(
        self,
        name: str,
        url: str,
        product_category: str,
        fallback_reason: str = "",
    ) -> tuple[SourceEvidence, dict]:
        start = time.perf_counter()
        evidence = self.fetch(name, url, product_category)
        return evidence, {
            "source_name": name,
            "adapter_name": self.adapter_name(name),
            "enabled": self.is_enabled(name),
            "fallback": bool(fallback_reason),
            "fallback_reason": fallback_reason,
            "fetch_latency_ms": (time.perf_counter() - start) * 1000,
            "source_type": evidence.source_type,
            "confidence": evidence.confidence,
        }
