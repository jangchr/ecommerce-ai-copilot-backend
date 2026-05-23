from schemas.source_contract import SourceEvidence
from source_adapters.base import BaseSourceAdapter


class AmazonReviewAdapter(BaseSourceAdapter):
    source_type = "amazon_review_api"

    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        return SourceEvidence(
            source_type="unavailable",
            source_url=url,
            product_category=product_category,
            data_warnings=["amazon_review_api_disabled"],
            metadata={"adapter": self.__class__.__name__, "enabled": False},
        )
