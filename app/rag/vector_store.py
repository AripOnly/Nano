# app/rag/vector_manager.py

import os
import faiss
from app.utils import FileManager
from .embedder import Embedder


class VectorStore:
    def __init__(self, dim=384):
        self.dim = dim
        self.embedder = Embedder()
        self.fm = FileManager()

        self.index = None
        self.metadata = []
        self.index_path = None
        self.metadata_path = None

    def _setup_paths(self, index_path: str):
        self.index_path = index_path
        self.metadata_path = index_path + ".meta.json"

        path_dir = os.path.dirname(index_path)
        if path_dir and not os.path.exists(path_dir):
            os.makedirs(path_dir)

    def _load_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatIP(self.dim)

    def _load_metadata(self):
        if os.path.exists(self.metadata_path):
            return self.fm.read_json(self.metadata_path)

    def _save_index(self):
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)

    def _save_metadata(self):
        if not os.path.exists(self.metadata_path):
            self.fm.create_json(self.metadata_path, self.metadata, overwrite=False)
        else:
            self.fm.append_json(self.metadata_path, self.metadata)

    def add_vector(self, text: str, metadata: dict, index_path: str):
        self._setup_paths(index_path)
        self._load_index()
        self._load_metadata()

        embedding = self.embedder.encode_text(text)

        self.index.add(embedding.astype("float32"))
        self.metadata.append(metadata)

        self._save_index()
        self._save_metadata()

        return {"status": "success", "added": metadata}

    def search(
        self, query_text: str, index_path: str, top_k: int = 5, min_score: float = 0.1
    ):
        self._setup_paths(index_path)
        self._load_index()
        self._load_metadata()

        if self.index is None or self.index.ntotal == 0 or not self.metadata:
            return []

        query_embedding = self.embedder.encode_text(query_text)

        D, I = self.index.search(query_embedding.astype("float32"), top_k)

        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(self.metadata) and score > min_score:
                result = self.metadata[idx].copy()
                result["score"] = float(score)
                results.append(result)

        return results
