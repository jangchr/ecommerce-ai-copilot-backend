from schemas.source_contract import SourceEvidence
from source_adapters.base import BaseSourceAdapter


class MockTrendAdapter(BaseSourceAdapter):
    source_type = "mock_trend_adapter"
    _CATEGORY_SIGNALS = {
        "balsamic_vinegar": [
            "Leak-proof packaging proof draws attention before taste claims.",
            "Texture contrast shots make thin glaze failures instantly visible.",
        ],
        "phone_case": [
            "Drop-test demonstrations make protection claims believable.",
            "Button feel and wireless charging proof reduce purchase hesitation.",
        ],
        "skincare_serum": [
            "Texture and skin-reaction proof matter more than abstract glow claims.",
            "Clean dispensing demonstrations address leakage and irritation anxiety.",
        ],
    }
    _DEFAULT_SIGNALS = [
        "Show the failure in use before introducing the relief moment.",
        "Use tactile before-and-after proof to make product claims credible.",
    ]

    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        signals = self._CATEGORY_SIGNALS.get(product_category, self._DEFAULT_SIGNALS)
        return SourceEvidence(
            source_type=self.source_type,
            source_url=url,
            product_category=product_category,
            confidence=0.35,
            trend_confidence=0.35,
            trend_signals=signals,
            data_warnings=["mock_trend_signal_used"],
            metadata={"adapter": self.__class__.__name__},
        )
