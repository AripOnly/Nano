# app/memory/relevant_memory.py

import os
from .base_memory import BaseMemory
from app.rag.vector_store import VectorStore
from app.utils import log


class RelevantMemory(BaseMemory):
    def __init__(
        self,
        top_k: int = 10,
        last_n: int = 10,
        max_tokens: int = 1024,
        min_score: float = 0.1,
    ):
        super().__init__()
        self.vm = VectorStore()
        self.top_k = top_k
        self.last_n = last_n
        self.max_tokens = max_tokens
        self.min_score = min_score

    def get_relevant_memory(self, prompt) -> str:
        recent = self.load_memory(last_n=self.last_n)
        recent_ids = {item["chat_id"] for item in recent}

        relevant = self.vm.search(
            prompt,
            index_path=self.memory_vector_file,
            top_k=self.top_k,
            min_score=self.min_score,
        )

        # 1️⃣ Filter duplikat ID
        filtered = [item for item in relevant if item.get("chat_id") not in recent_ids]

        # 2️⃣ Token filtering
        filtered = self.filter_memory(
            data=filtered,
            max_tokens=self.max_tokens,
            sort_by_score=True,
        )

        return self.format_str(filtered)
