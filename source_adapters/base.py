from abc import ABC, abstractmethod

from schemas.source_contract import SourceEvidence


class BaseSourceAdapter(ABC):
    source_type: str

    @abstractmethod
    def fetch(self, url: str, product_category: str) -> SourceEvidence:
        raise NotImplementedError
