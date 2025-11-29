# app/memory/recent_memory.py

from .base_memory import BaseMemory


class RecentMemory(BaseMemory):
    def __init__(self, last_n: int = 10, max_tokens: int = 2048):
        super().__init__()
        self.last_n = last_n
        self.max_tokens = max_tokens

    def get_recent_memory(self) -> str:
        records = self.load_memory(last_n=self.last_n)

        # Selalu pertahankan dict terbaru
        records = self.filter_memory(
            data=records,
            max_tokens=self.max_tokens,
            sort_by_score=False,  # recent tidak pakai score
        )

        return self.format_str(records)
