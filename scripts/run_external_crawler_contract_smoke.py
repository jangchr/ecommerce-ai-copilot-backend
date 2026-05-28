import json
import os
import sys
import threading
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_fake_amazon_crawler_worker import FakeAmazonCrawlerHandler
from source_adapters.amazon_review_adapter import AmazonReviewAdapter


def main() -> None:
    server = HTTPServer(("127.0.0.1", 0), FakeAmazonCrawlerHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    endpoint = f"http://127.0.0.1:{port}/amazon"
    os.environ["AMAZON_CRAWLER_MODE"] = "external"
    os.environ["AMAZON_EXTERNAL_CRAWLER_URL"] = endpoint

    try:
        evidence = AmazonReviewAdapter().fetch(
            "https://www.amazon.com/dp/B000FAKE01",
            "amazon_product",
        )

        print("crawler_mode:", os.getenv("AMAZON_CRAWLER_MODE"))
        print("external_endpoint:", endpoint)
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

        if evidence.source_type != "amazon_review_api":
            raise SystemExit("External crawler contract smoke failed: source_type is not amazon_review_api.")
        if len(evidence.reviews) < 3:
            raise SystemExit("External crawler contract smoke failed: expected at least 3 review records.")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
