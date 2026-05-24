import unittest
from unittest.mock import patch

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
      Grocery & Gourmet Food › Vinegars
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
            "https://www.amazon.com/dp/B000TEST",
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
        self.assertEqual(metadata["rating"], "4.4")
        self.assertEqual(metadata["review_count"], "1,234")
        self.assertEqual(metadata["price"], "$14.99")
        self.assertIn("Vinegars", metadata["category_hint"])
        self.assertIn("Thick glaze for salads and cheese boards.", metadata["bullet_points"])

    def test_fetch_uses_mocked_network_response(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", return_value=AMAZON_HTML):
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST", "balsamic_vinegar")

        self.assertEqual(evidence.source_type, "amazon_review_api")
        self.assertGreaterEqual(evidence.confidence, 0.70)

    def test_fetch_failure_returns_unavailable_with_error(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=TimeoutError("timeout")):
            evidence = adapter.fetch("https://www.amazon.com/dp/B000TEST", "balsamic_vinegar")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("amazon_fetch_failed", evidence.data_warnings)
        self.assertIn("timeout", evidence.metadata["error"])

    def test_non_amazon_url_returns_unavailable_without_network(self):
        adapter = AmazonReviewAdapter()
        with patch.object(adapter, "_fetch_html", side_effect=AssertionError("must not fetch")):
            evidence = adapter.fetch("https://example.com/product", "balsamic_vinegar")

        self.assertEqual(evidence.source_type, "unavailable")
        self.assertIn("non_amazon_url", evidence.data_warnings)


if __name__ == "__main__":
    unittest.main()
