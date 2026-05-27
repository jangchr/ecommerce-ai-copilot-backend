import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

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


    def test_parse_html_cleans_mojibake_category_separators(self):
        adapter = AmazonReviewAdapter()
        separator = chr(0x00E2) + chr(0x00BA)
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
