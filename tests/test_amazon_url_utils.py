import unittest

from source_adapters.amazon_url_utils import (
    extract_amazon_asin_from_path,
    normalize_amazon_product_url,
)


class AmazonURLUtilsTest(unittest.TestCase):
    def test_extracts_asin_from_dp_url(self):
        result = normalize_amazon_product_url("https://www.amazon.com/dp/B000TEST00")

        self.assertTrue(result.is_supported)
        self.assertEqual(result.asin, "B000TEST00")
        self.assertEqual(result.normalized_url, "https://www.amazon.com/dp/B000TEST00")
        self.assertEqual(result.source_type, "amazon_product_url")

    def test_extracts_asin_from_slug_dp_url_and_removes_query(self):
        result = normalize_amazon_product_url(
            "https://www.amazon.com/Premium-Product-Name/dp/B000TEST00?tag=demo"
        )

        self.assertTrue(result.is_supported)
        self.assertEqual(result.asin, "B000TEST00")
        self.assertEqual(result.normalized_url, "https://www.amazon.com/dp/B000TEST00")

    def test_extracts_asin_from_gp_product_url(self):
        result = normalize_amazon_product_url("https://www.amazon.com/gp/product/B000TEST00/ref=something")

        self.assertTrue(result.is_supported)
        self.assertEqual(result.asin, "B000TEST00")

    def test_accepts_amazon_dot_com_without_scheme(self):
        result = normalize_amazon_product_url("www.amazon.com/dp/B000TEST00")

        self.assertTrue(result.is_supported)
        self.assertEqual(result.normalized_url, "https://www.amazon.com/dp/B000TEST00")

    def test_uppercases_lowercase_asin(self):
        result = normalize_amazon_product_url("https://amazon.com/dp/b000test00")

        self.assertTrue(result.is_supported)
        self.assertEqual(result.asin, "B000TEST00")

    def test_rejects_non_amazon_com_url(self):
        result = normalize_amazon_product_url("https://example.com/dp/B000TEST00")

        self.assertFalse(result.is_supported)
        self.assertEqual(result.reason, "non_amazon_com_url")
        self.assertEqual(result.source_type, "unsupported_url")

    def test_rejects_international_amazon_for_demo_scope(self):
        result = normalize_amazon_product_url("https://www.amazon.co.uk/dp/B000TEST00")

        self.assertFalse(result.is_supported)
        self.assertEqual(result.reason, "non_amazon_com_url")

    def test_rejects_amazon_search_url(self):
        result = normalize_amazon_product_url("https://www.amazon.com/s?k=printer")

        self.assertFalse(result.is_supported)
        self.assertEqual(result.reason, "not_amazon_product_detail_url")

    def test_missing_url_is_unsupported(self):
        result = normalize_amazon_product_url("")

        self.assertFalse(result.is_supported)
        self.assertEqual(result.reason, "missing_url")

    def test_path_helper_returns_empty_for_invalid_paths(self):
        self.assertEqual(extract_amazon_asin_from_path("/s"), "")
        self.assertEqual(extract_amazon_asin_from_path("/dp/SHORT"), "")


if __name__ == "__main__":
    unittest.main()
