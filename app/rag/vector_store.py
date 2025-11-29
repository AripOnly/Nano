# app/rag/vector_store.py

import os
import faiss
import numpy as np
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
            os.makedirs(path_dir, exist_ok=True)

    def _load_index(self):
        # Load existing index if present, otherwise create a new IndexFlatIP
        if self.index_path and os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
            except Exception:
                # fallback: create a new index if read fails
                self.index = faiss.IndexFlatIP(self.dim)
        else:
            self.index = faiss.IndexFlatIP(self.dim)

    def _load_metadata(self):
        # Load metadata from JSON file and normalize to a list
        if self.metadata_path and os.path.exists(self.metadata_path):
            data = self.fm.read_json(self.metadata_path)
            # JSONFileManager returns standardized dict on error/warning
            if isinstance(data, dict) and data.get("status") in ("error", "warning"):
                self.metadata = []
            else:
                # Expecting a list of metadata records
                if isinstance(data, list):
                    self.metadata = data
                else:
                    # If it's a dict, convert to list (backwards compatibility)
                    self.metadata = [data]
        else:
            self.metadata = []

    def _save_index(self):
        if self.index is not None and self.index_path:
            faiss.write_index(self.index, self.index_path)

    def _save_metadata(self):
        # Always write the current metadata list (overwrite) to keep it consistent
        if self.metadata_path:
            try:
                self.fm.write_json(self.metadata_path, self.metadata, safe_mode=True)
            except Exception:
                # fallback to create_json if write fails for some reason
                try:
                    self.fm.create_json(self.metadata_path, self.metadata, overwrite=True)
                except Exception:
                    pass

    def add_vector(self, text: str, metadata: dict, index_path: str):
        self._setup_paths(index_path)
        self._load_index()
        self._load_metadata()

        embedding = self.embedder.encode_text(text)

        # Ensure embeddings shape is (n, dim) and dtype float32
        if isinstance(embedding, np.ndarray):
            vec = embedding.astype("float32")
            if vec.ndim == 1:
                vec = np.expand_dims(vec, axis=0)
        else:
            # convert to numpy array
            vec = np.array(embedding, dtype="float32")
            if vec.ndim == 1:
                vec = np.expand_dims(vec, axis=0)

        # Validate dimension
        if vec.shape[1] != self.dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dim}, got {vec.shape[1]}")

        # Add to index and metadata
        self.index.add(vec)
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

        if self.index is None or getattr(self.index, "ntotal", 0) == 0 or not self.metadata:
            return []

        query_embedding = self.embedder.encode_text(query_text)

        # Ensure shape and dtype for FAISS search
        if isinstance(query_embedding, np.ndarray):
            q = query_embedding.astype("float32")
            if q.ndim == 1:
                q = np.expand_dims(q, axis=0)
        else:
            q = np.array(query_embedding, dtype="float32")
            if q.ndim == 1:
                q = np.expand_dims(q, axis=0)

        D, I = self.index.search(q, top_k)

        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(self.metadata) and score > min_score:
                # defensive copy
                meta = self.metadata[idx].copy() if isinstance(self.metadata[idx], dict) else {"value": self.metadata[idx]}
                meta["score"] = float(score)
                results.append(meta)

        return results
