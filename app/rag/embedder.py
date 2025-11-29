# app/rag/embedding_manager.py

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode_text(self, text: str | list[str]) -> np.ndarray:
        if isinstance(text, str):
            text = [text]

        embeddings = self.model.encode(text)
        return self._normalize(embeddings)

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms
