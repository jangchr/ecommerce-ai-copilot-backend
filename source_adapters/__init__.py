"""Grounded evidence source adapters."""

from source_adapters.amazon_review_adapter import AmazonReviewAdapter
from source_adapters.local_review_adapter import LocalReviewAdapter
from source_adapters.mock_trend_adapter import MockTrendAdapter
from source_adapters.reddit_review_adapter import RedditReviewAdapter
from source_adapters.registry import SourceAdapterRegistry
from source_adapters.tiktok_trend_adapter import TikTokTrendAdapter

__all__ = [
    "AmazonReviewAdapter",
    "LocalReviewAdapter",
    "MockTrendAdapter",
    "RedditReviewAdapter",
    "SourceAdapterRegistry",
    "TikTokTrendAdapter",
]
