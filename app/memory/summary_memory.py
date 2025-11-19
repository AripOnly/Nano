# app/memory/summary_memory.py

from .base_summarizer import BaseSummarizer
from app.rag.vector_store import VectorStore


class SummaryMemory(BaseSummarizer):
    def __init__(
        self,
        top_k: int = 3,
        max_tokens: int = 1024,
        min_score: float = 0.1,
    ):
        super().__init__()
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.min_score = min_score

        self.vm = VectorStore()

    def get_summary_memory(
        self,
        prompt: str,
    ) -> str:
        """
        Cari summary relevan dari vector store berdasar prompt, filter token, kembalikan string.
        """
        # Ambil top_k summary dari vector store
        relevant = self.vm.search(
            prompt,
            index_path=self.summary_vector_file,
            top_k=self.top_k,
            min_score=self.min_score,
        )

        # Filter summary berdasarkan token
        filtered = self.filter_summary(
            data=relevant,
            max_tokens=self.max_tokens,
            sort_by_score=True,
        )

        return self.summary_str(filtered)
