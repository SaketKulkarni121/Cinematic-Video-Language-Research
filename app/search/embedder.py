from abc import ABC, abstractmethod
import numpy as np
import os
from typing import Optional, List


class Embedder(ABC):
    @abstractmethod
    def embed(self, text: str) -> Optional[List[float]]:
        pass


class MockEmbedder(Embedder):
    def embed(self, text: str) -> Optional[List[float]]:
        # TODO: Implement actual embedding logic
        # Didn't want to use a real embedder for now
        if os.getenv("EMBEDDER") == "mock":
            return list(np.random.normal(0, 1, 768))
        return None


def get_embedder() -> Embedder:
    return MockEmbedder()
