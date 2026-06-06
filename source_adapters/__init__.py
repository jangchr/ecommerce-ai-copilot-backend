"""Grounded evidence source adapters."""

from source_adapters.amazon_crawler import AmazonCrawlerResult, ExternalAmazonCrawler, HybridAmazonCrawler, RequestsAmazonCrawler
from source_adapters.amazon_review_adapter import AmazonReviewAdapter
from source_adapters.local_review_adapter import LocalReviewAdapter
from source_adapters.mock_trend_adapter import MockTrendAdapter
from source_adapters.reddit_review_adapter import RedditReviewAdapter
from source_adapters.registry import SourceAdapterRegistry
from source_adapters.tiktok_trend_adapter import TikTokTrendAdapter
from source_adapters.project_sources import (
    build_project_source,
    build_source_evidence_artifact,
    build_source_quality_gate,
    build_source_snapshot,
    classify_review_snippet,
    dedupe_review_snippets,
    detect_source_type_from_url,
    normalize_project_source_url,
    normalize_review_batch,
    parse_amazon_asin,
    parse_shopify_handle,
)

__all__ = [
    "AmazonCrawlerResult",
    "ExternalAmazonCrawler",
    "HybridAmazonCrawler",
    "AmazonReviewAdapter",
    "RequestsAmazonCrawler",
    "LocalReviewAdapter",
    "MockTrendAdapter",
    "RedditReviewAdapter",
    "SourceAdapterRegistry",
    "TikTokTrendAdapter",
    "build_project_source",
    "build_source_evidence_artifact",
    "build_source_quality_gate",
    "build_source_snapshot",
    "classify_review_snippet",
    "dedupe_review_snippets",
    "detect_source_type_from_url",
    "normalize_project_source_url",
    "normalize_review_batch",
    "parse_amazon_asin",
    "parse_shopify_handle",
]
