import json
import re
from pathlib import Path

from schemas.source_contract import ReviewRecord, SourceEvidence
from source_adapters.base import BaseSourceAdapter


class LocalReviewAdapter(BaseSourceAdapter):
    source_type = "local_review_dataset"

    def __init__(self, dataset_dir: Path | str = Path("data/reviews")):
        self.dataset_dir = Path(dataset_dir)

    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        category = self._safe_category(product_category)
        file_path = self.dataset_dir / f"{category}.json" if category else None
        if file_path is None or not file_path.exists():
            return SourceEvidence(
                source_type="unavailable",
                source_url=url,
                product_category=product_category,
                data_warnings=["missing_local_review_dataset"],
            )

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
            reviews = [ReviewRecord.model_validate(item) for item in raw.get("reviews", [])]
        except (OSError, ValueError, TypeError):
            return SourceEvidence(
                source_type="unavailable",
                source_url=str(file_path),
                product_category=product_category,
                data_warnings=["invalid_local_review_dataset"],
            )

        return SourceEvidence(
            source_type=self.source_type,
            source_url=str(file_path),
            product_category=str(raw.get("product_category", product_category)),
            confidence=0.75,
            review_confidence=0.75,
            trend_confidence=0.35,
            review_count=len(reviews),
            reviews=reviews,
            evidence_quotes=[review.text for review in reviews if review.text][:6],
            data_warnings=["local_curated_review_dataset_used"],
            metadata={"adapter": self.__class__.__name__},
        )

    @staticmethod
    def _safe_category(value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_")
        if not re.fullmatch(r"[a-z0-9_-]+", normalized):
            return ""
        return normalized
