import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_adapters.amazon_review_adapter import AmazonReviewAdapter


def main() -> None:
    url = os.getenv("AMAZON_SMOKE_URL", "https://www.amazon.com/dp/B00QIIMCCW")
    category = os.getenv("AMAZON_SMOKE_CATEGORY", "amazon_product")
    mode = os.getenv("AMAZON_CRAWLER_MODE", "requests")

    evidence = AmazonReviewAdapter().fetch(url, category)

    print("crawler_mode:", mode)
    print("source_type:", evidence.source_type)
    print("confidence:", evidence.confidence)
    print("warnings:", evidence.data_warnings)
    print("title:", evidence.metadata.get("product_title"))
    print("price:", evidence.metadata.get("price"))
    print("rating:", evidence.metadata.get("rating"))
    print("review_count:", evidence.metadata.get("review_count"))
    print("bullets_count:", len(evidence.metadata.get("bullet_points") or []))
    print("reviews_count:", len(evidence.reviews))
    for review in evidence.reviews[:8]:
        print("-", review.text)


if __name__ == "__main__":
    main()
