# app/utils/summary_file_manager.py

import os
from app.rag.vector_store import VectorStore
from app.utils import FileManager, token_count, log, generate_id, get_current_time
from app.services.model_openai import ModelOpenAI


class BaseSummarizer:
    def __init__(self):
        self.memory_root = "app/data/memory/default/"
        self.vector_root = "app/data/vector_store/memory/default/"

        self.summary_file = os.path.join(self.memory_root, "summary.json")
        self.count_summary_file = os.path.join(self.memory_root, "count_summary.json")
        self.summary_vector_file = os.path.join(self.vector_root, "summary.index")

        self.vector = VectorStore()
        self.fm = FileManager()
        self.model = ModelOpenAI("gpt-4o-mini")

    def load_summary(self, last_n: int = None) -> list[dict]:
        if not os.path.exists(self.summary_file):
            log.error(f"Summary file '{self.summary_file}' does not exist.")
            return []

        data = self.fm.read_json(self.summary_file)
        if not isinstance(data, list):
            log.error("Summary file content is invalid (expected list).")
            return []

        if isinstance(last_n, int):
            return data[-last_n:]

    def save_summary(self, summary_data=[]):
        self.summary_file = os.path.join(self.memory_root, "summary.json")

        if os.path.exists(self.summary_file):
            self.fm.append_json(self.summary_file, summary_data)
            return True
        else:
            return False

    def summary_str(self, data: list[dict]) -> str:
        if not data:
            return ""
        blocks = []
        for s in data:
            blocks.append(f"Date: {s.get('date')}\nSummary: {s.get('summary')}")
        return "\n\n".join(blocks)

    def filter_summary(
        self, data: list[dict], max_tokens: int = 1000, sort_by_score=True
    ):
        if not data:
            return []

        records = data.copy()

        if sort_by_score:
            records.sort(key=lambda x: x.get("score", 0), reverse=True)

        def total_tokens(items):
            return token_count(self.summary_str(items))

        while total_tokens(records) > max_tokens:
            if len(records) <= 1:
                break
            records.pop(-1)

        return records

    def get_counter(self):
        if os.path.exists(self.count_summary_file):
            counter_data = self.fm.read_json(self.count_summary_file)
            if isinstance(counter_data, dict):
                return counter_data.get("count", 0)
        return 0

    def increment_counter(self):
        counter = self.get_counter() + 1
        counter_data = {"count": counter}
        self.fm.write_json(self.count_summary_file, counter_data)

        return counter

    def reset_counter(self):
        counter_data = {"count": 0}
        self.fm.write_json(self.count_summary_file, counter_data)
        return True

    def create_summary(self, prompt: str, text: str):
        prompt_system = (
            "You are a summarization assistant.\n"
            "Your task is to read a conversation between a user and an AI, then produce a concise factual summary in plain paragraph form.\n"
            "Guidelines:\n"
            "- Focus only on the main questions, answers, and key facts.\n"
            "- Keep the tone neutral and objective.\n"
            "- Do not include greetings or small talk unless critical for context.\n"
            "- Output must be a single short paragraph (3–5 sentences).\n"
            "- The goal is to make the summary usable as memory recall that can be provided back to the AI model.\n"
        )

        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": text},
        ]

        response = self.model.call(messages=messages)

        summary_data = {
            "summary_id": generate_id("smr"),
            "summary": response.output_text,
            "date": get_current_time(),
        }

        self.save_summary(summary_data)

        vector_summary_file = os.path.join(self.vector_root, "summary.index")
        self.vector.add_vector(prompt, summary_data, vector_summary_file)
