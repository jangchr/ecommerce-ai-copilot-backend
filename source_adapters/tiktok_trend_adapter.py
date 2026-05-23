from schemas.source_contract import SourceEvidence
from source_adapters.base import BaseSourceAdapter


class TikTokTrendAdapter(BaseSourceAdapter):
    source_type = "tiktok_trend_api"

    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        return SourceEvidence(
            source_type="unavailable",
            source_url=url,
            product_category=product_category,
            data_warnings=["tiktok_trend_api_disabled"],
            metadata={"adapter": self.__class__.__name__, "enabled": False},
        )
