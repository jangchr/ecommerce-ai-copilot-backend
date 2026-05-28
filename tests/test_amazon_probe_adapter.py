import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from source_adapters.amazon_crawler import AmazonCrawlerResult, RequestsAmazonCrawler
from source_adapters.amazon_review_adapter import AmazonReviewAdapter


AMAZON_HTML = """
<html>
  <head>
    <meta property="og:title" content="Fallback Product Title" />
  </head>
  <body>
    <span id="productTitle">Premium Balsamic Glaze</span>
    <span class="a-icon-alt">4.4 out of 5 stars</span>
    <span id="acrCustomerReviewText">1,234 ratings</span>
    <span class="a-price a-offscreen">$14.99</span>
    <div id="wayfinding-breadcrumbs_feature_div">
      Grocery & Gourmet Food > Vinegars
    </div>
    <div id="feature-bullets">
      <ul>
        <li><span>Thick glaze for salads and cheese boards.</span></li>
        <li><span>Resealable bottle designed to reduce leaks.</span></li>
      </ul>
    </div>
    <span data-hook="review-body">
      The cap cracked during shipping and leaked all over the box.
    </span>
    <span class="review-text-content">
      The glaze was too watery and ran off the salad instead of sticking.
    </span>
  </body>
</html>
"""


class AmazonProbeAdapterTest(unittest.TestCase):
    def test_parse_html_extracts_product_and_review_evidence(self):
        evidence = AmazonReviewAdapter().parse_html(
            AMAZON_HTML,
            "https://www.amazon.com/dp/B000TEST00",
            "balsamic_vinegar",
        )

        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertGreaterEqual(evidence.confidence, 0.70)
        self.assertEqual(evidence.review_confidence, evidence.confidence)
        self.assertEqual(evidence.review_count, 1234)
        self.assertIn("cap cracked", " ".join(evidence.evidence_quotes))
        self.assertTrue(evidence.reviews)
        self.assertIn("cap cracked", evidence.reviews[0].text)
        self.assertEqual(evidence.reviews[0].source, "amazon_review_snippet")
        self.assertLessEqual(max(len(quote) for quote in evidence.evidence_quotes), 240)

        metadata = evidence.metadata
        self.assertEqual(metadata["product_title"], "Premium Balsamic Glaze")
        self.assertEqual(metadata["asin"], "B000TEST00")
        self.assertEqual(metadata["normalized_url"], "https://www.amazon.com/dp/B000TEST00")
        self.assertEqual(metadata["intake_status"], "supported")
        self.assertEqual(metadata["intake_source_type"], "amazon_product_url")
        self.assertEqual(metadata["rating"], "4.4")
        self.assertEqual(metadata["review_count"], "1,234")
        self.assertEqual(metadata["price"], "$14.99")
        self.assertIn("Vinegars", metadata["category_hint"])
        self.assertIn("Thick glaze for salads and cheese boards.", metadata["bullet_points"])



    def test_parse_html_cleans_amazon_review_ui_noise(self):
        noisy_html = AMAZON_HTML.replace(
            "The cap cracked during shipping and leaked all over the box.",
            """
            Brief content visible, double tap to read full content.
            Full content visible, double tap to read brief content.
            The cap cracked during shipping and leaked all over the box.
            Read more Read less
            """,
        )

        evidence = AmazonReviewAdapter().parse_html(
            noisy_html,
            "https://www.amazon.com/dp/B000TEST00",
            "balsamic_vinegar",
        )

        combined = " ".join(evidence.evidence_quotes + [review.text for review in evidence.reviews])
        self.assertIn("cap cracked during shipping", combined)
        self.assertNotIn("Brief content visible", combined)
        self.assertNotIn("Full content visible", combined)
        self.assertNotIn("Read more Read less", combined)
        self.assertTrue(all(review.text for review in evidence.reviews))


    def test_parse_html_cleans_mojibake_category_separators(self):
        adapter = AmazonReviewAdapter()
        cases = [
            chr(0x00E2) + chr(0x00BA),
            chr(0x00E2) + chr(0x0080) + chr(0x00BA),
            chr(0x00E2) + chr(0x20AC) + chr(0x00BA),
        ]

        for separator in cases:
            with self.subTest(separator=[hex(ord(ch)) for ch in separator]):
                html_text = AMAZON_HTML.replace(
                    "Grocery & Gourmet Food > Vinegars",
                    f"Grocery & Gourmet Food {separator} Pantry Staples {separator} Balsamic",
                )

                evidence = adapter.parse_html(
                    html_text,
                    "https://www.amazon.com/dp/B000TEST00",
                    "balsamic_vinegar",
                )

                self.assertEqual(
                    evidence.metadata["category_hint"],
                    "Grocery & Gourmet Food > Pantry Staples > Balsamic",
                )


    def test_parse_html_uses_fallback_patterns_for_sparse_amazon_html(self):
        sparse_html = """
        <html>
          <head>
            <script type="application/ld+json">
              {
                "@type": "Product",
                "name": "JSON Silicone Can Strainer",
                "offers": {"price": "8.99"},
                "aggregateRating": {"ratingValue": "4.6", "reviewCount": "485"}
              }
            </script>
          </head>
          <body>
            <span id="acrPopover" title="4.6 out of 5 stars"></span>
            <span data-hook="total-review-count">485 global ratings</span>
            <span class="a-offscreen">$8.99</span>
            <div id="feature-bullets">
              <ul>
                <li><span>Flexible silicone strainer clips onto cans.</span></li>
                <li><span>Compact kitchen gadget for draining beans and tuna.</span></li>
              </ul>
            </div>
            <span data-hook="review-title">Easy to attach</span>
            <span data-hook="review-body">
              I love this. Easy to put on and remove.
            </span>
            <span class="review-text-content">
              Keeps beans from falling into the sink.
            </span>
          </body>
        </html>
        """

        evidence = AmazonReviewAdapter().parse_html(
            sparse_html,
            "https://www.amazon.com/dp/B000TEST00",
            "amazon_product",
        )

        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertGreaterEqual(evidence.confidence, 0.70)
        self.assertEqual(evidence.review_count, 485)

        metadata = evidence.metadata
        self.assertEqual(metadata["product_title"], "JSON Silicone Can Strainer")
        self.assertEqual(metadata["rating"], "4.6")
        self.assertEqual(metadata["review_count"], "485")
        self.assertEqual(metadata["price"], "$8.99")
        self.assertIn("Flexible silicone strainer", " ".join(metadata["bullet_points"]))

        combined = " ".join(evidence.evidence_quotes + [review.text for review in evidence.reviews])
        self.assertIn("Easy to put on and remove", combined)
        self.assertIn("Keeps beans from falling", combined)
        self.assertNotIn("missing_price", evidence.data_warnings)

    def test_parse_html_reports_partial_parse_quality_warnings(self):
        partial_html = """
        <html>
          <body>
            <span id="productTitle">Minimal Product Page</span>
            <span class="a-icon-alt">4.2 out of 5 stars</span>
          </body>
        </html>
        """

        evidence = AmazonReviewAdapter().parse_html(
            partial_html,
            "https://www.amazon.com/dp/B000TEST00",
            "amazon_product",
        )

        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertIn("Minimal Product Page", evidence.evidence_quotes)
        self.assertIn("missing_price", evidence.data_warnings)
        self.assertIn("missing_bullet_points", evidence.data_warnings)
        self.assertIn("sparse_reviews", evidence.data_warnings)
        self.assertIn("partial_parse", evidence.data_warnings)



    def test_fetch_uses_injected_crawler_execution_layer(self):
        class FakeCrawler:
            crawler_name = "fake_amazon_crawler"

            def __init__(self):
                self.urls = []

            def fetch_html(self, url):
                self.urls.append(url)
                return AmazonCrawlerResult(
                    url=url,
                    html=AMAZON_HTML,
                    status_code=200,
                    final_url=url,
                    crawler_name=self.crawler_name,
                )

        crawler = FakeCrawler()
        adapter = AmazonReviewAdapter(crawler=crawler)

        evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "balsamic_vinegar")

        self.assertEqual(crawler.urls[0], "https://www.amazon.com/dp/B000TEST00")
        review_urls = [
            url for url in crawler.urls
            if "/product-reviews/B000TEST00" in url or "/hz/reviews-render/" in url
        ]
        self.assertGreaterEqual(len(review_urls), 2)
        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertEqual(evidence.metadata["product_title"], "Premium Balsamic Glaze")
        self.assertIn("cap cracked", " ".join(evidence.evidence_quotes))


    def test_fetch_merges_product_reviews_page_for_review_snippets(self):
        product_html = """
        <html>
          <body>
            <span id="productTitle">Review Page Merge Product</span>
            <span class="a-icon-alt">4.5 out of 5 stars</span>
            <span id="acrCustomerReviewText">120 ratings</span>
            <div id="feature-bullets"><ul><li><span>Compact product bullet.</span></li></ul></div>
          </body>
        </html>
        """
        reviews_html = """
        <html>
          <body>
            <span data-hook="review-body">Easy to use and it saves time every day.</span>
            <span data-hook="review-body">The small size makes it easier to store.</span>
          </body>
        </html>
        """

        class FakeCrawler:
            def __init__(self):
                self.urls = []

            def fetch_html(self, url):
                self.urls.append(url)
                html = reviews_html if ("/product-reviews/" in url or "/hz/reviews-render/" in url) else product_html
                return AmazonCrawlerResult(url=url, html=html, status_code=200, final_url=url)

        crawler = FakeCrawler()
        evidence = AmazonReviewAdapter(crawler=crawler).fetch(
            "https://www.amazon.com/dp/B000TEST00",
            "amazon_product",
        )

        review_urls = [
            url for url in crawler.urls
            if "/product-reviews/B000TEST00" in url or "/hz/reviews-render/" in url
        ]
        self.assertGreaterEqual(len(review_urls), 2)
        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertEqual(len(evidence.reviews), 2)
        combined = " ".join(review.text for review in evidence.reviews)
        self.assertIn("Easy to use and it saves time", combined)
        self.assertIn("small size makes it easier", combined)
        self.assertNotIn("sparse_reviews", evidence.data_warnings)



    def test_fetch_attempts_multiple_review_page_fallbacks(self):
        class FakeCrawler:
            def __init__(self):
                self.urls = []

            def fetch_html(self, url):
                self.urls.append(url)
                html = AMAZON_HTML
                return AmazonCrawlerResult(url=url, html=html, status_code=200, final_url=url)

        crawler = FakeCrawler()
        evidence = AmazonReviewAdapter(crawler=crawler).fetch(
            "https://www.amazon.com/dp/B000TEST00",
            "amazon_product",
        )

        review_urls = [
            url for url in crawler.urls
            if "/product-reviews/B000TEST00" in url or "/hz/reviews-render/" in url
        ]
        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertGreaterEqual(len(review_urls), 2)


    def test_requests_crawler_converts_http_error_for_adapter_classification(self):
        adapter = AmazonReviewAdapter(crawler=RequestsAmazonCrawler())

        with patch("source_adapters.amazon_crawler.requests.get") as get:
            response = get.return_value
            response.status_code = 404
            response.reason = "Not Found"
            response.url = "https://www.amazon.com/dp/B000MISSNG"
            response.headers = {}
            response.text = ""

            evidence = adapter.fetch("https://www.amazon.com/dp/B000MISSNG", "amazon_product")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("not_found", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "not_found")


    def test_fetch_uses_mocked_network_response(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", return_value=AMAZON_HTML):
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "balsamic_vinegar")

        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertGreaterEqual(evidence.confidence, 0.70)

    def test_fetch_failure_returns_unavailable_with_error(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=TimeoutError("timeout")):
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "balsamic_vinegar")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("timeout", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "timeout")
        self.assertEqual(evidence.metadata["retry_count"], 1)
        self.assertIn("timeout", evidence.metadata["error"])

    def test_non_amazon_url_returns_unavailable_without_network(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=AssertionError("must not fetch")):
            evidence = adapter.fetch("https://example.com/product", "balsamic_vinegar")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertEqual(evidence.metadata["intake_status"], "unsupported")
        self.assertEqual(evidence.metadata["intake_reason"], "non_amazon_com_url")
        self.assertIn("non_amazon_url", evidence.data_warnings)
        self.assertIn("invalid_or_redirected_url", evidence.data_warnings)

    def test_amazon_non_detail_url_returns_invalid_without_network(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=AssertionError("must not fetch")):
            evidence = adapter.fetch("https://www.amazon.com/s?k=printer", "printer")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertEqual(evidence.metadata["intake_status"], "unsupported")
        self.assertEqual(evidence.metadata["intake_reason"], "not_amazon_product_detail_url")
        self.assertIn("invalid_or_redirected_url", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "invalid_or_redirected_url")

    def test_404_does_not_retry_and_is_classified_as_not_found(self):
        adapter = AmazonReviewAdapter()
        error = HTTPError(
            "https://www.amazon.com/dp/B000MISSNG",
            404,
            "Not Found",
            hdrs=None,
            fp=None,
        )
        with patch.object(adapter, "_fetch_html", side_effect=error) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000MISSNG", "skincare_serum")

        self.assertEqual(fetch_html.call_count, 1)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("not_found", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "not_found")
        self.assertEqual(evidence.metadata["retry_count"], 0)

    def test_connection_reset_retries_once_and_can_succeed(self):
        adapter = AmazonReviewAdapter()
        with patch.object(
            adapter,
            "_fetch_html",
            side_effect=[ConnectionResetError("WinError 10054"), AMAZON_HTML],
        ) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "balsamic_vinegar")

        self.assertEqual(fetch_html.call_count, 2)
        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertEqual(evidence.metadata["retry_count"], 1)

    def test_connection_reset_after_retry_is_classified(self):
        adapter = AmazonReviewAdapter()
        with patch.object(
            adapter,
            "_fetch_html",
            side_effect=ConnectionResetError("WinError 10054 connection reset"),
        ) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "balsamic_vinegar")

        self.assertEqual(fetch_html.call_count, 2)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("transient_connection_reset", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "transient_connection_reset")
        self.assertEqual(evidence.metadata["retry_count"], 1)

    def test_url_error_connection_refused_retries_once_and_is_classified(self):
        adapter = AmazonReviewAdapter()
        refused = ConnectionRefusedError(
            10061,
            "No connection could be made because the target machine actively refused it",
        )
        with patch.object(adapter, "_fetch_html", side_effect=URLError(refused)) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "printer")

        self.assertEqual(fetch_html.call_count, 2)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("connection_refused", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "connection_refused")
        self.assertEqual(evidence.metadata["retry_count"], 1)

    def test_urllib_error_text_with_winerror_10061_classifies_connection_refused(self):
        adapter = AmazonReviewAdapter()
        error = URLError("[WinError 10061] connection refused")

        with patch.object(adapter, "_fetch_html", side_effect=error) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "balsamic_vinegar")

        self.assertEqual(fetch_html.call_count, 2)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertEqual(evidence.metadata["error_type"], "connection_refused")
        self.assertEqual(evidence.metadata["retry_count"], 1)
        self.assertIn("connection_refused", evidence.data_warnings)

    def test_url_error_winerror_10054_is_connection_reset(self):
        adapter = AmazonReviewAdapter()
        reset = URLError("[WinError 10054] An existing connection was forcibly closed by the remote host")
        with patch.object(adapter, "_fetch_html", side_effect=reset) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "printer")

        self.assertEqual(fetch_html.call_count, 2)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("transient_connection_reset", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "transient_connection_reset")
        self.assertEqual(evidence.metadata["retry_count"], 1)

    def test_url_error_timeout_is_timeout(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=URLError(TimeoutError("timed out"))) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "printer")

        self.assertEqual(fetch_html.call_count, 2)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("timeout", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "timeout")
        self.assertEqual(evidence.metadata["retry_count"], 1)

    def test_other_url_error_is_classified_without_retry(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=URLError("unknown url failure")) as fetch_html:
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "printer")

        self.assertEqual(fetch_html.call_count, 1)
        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("url_error", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "url_error")
        self.assertEqual(evidence.metadata["retry_count"], 0)

    def test_blocked_html_is_classified_as_blocked(self):
        adapter = AmazonReviewAdapter()
        blocked_html = "<html><body>Robot Check CAPTCHA enter the characters you see below</body></html>"
        with patch.object(adapter, "_fetch_html", return_value=blocked_html):
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "printer")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("blocked", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "blocked")

    def test_parse_empty_is_classified(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", return_value="<html><body>No usable fields</body></html>"):
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST00", "printer")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("parse_empty", evidence.data_warnings)
        self.assertEqual(evidence.metadata["error_type"], "parse_empty")


if __name__ == "__main__":
    unittest.main()
