# app/memory/memory_manager.py

import os
from app.utils import FileManager, generate_id, get_current_time, log, token_count
from app.rag.vector_store import VectorStore


class BaseMemory:
    def __init__(self):
        self.fm = FileManager()
        self.vm = VectorStore()
        self.root_memory = "app/data/memory/default/"
        self.root_vector = "app/data/vector_store/memory/default/"

        self.memory_file = os.path.join(self.root_memory, "memory.json")
        self.summary_file = os.path.join(self.root_memory, "summary.json")
        self.count_summary_file = os.path.join(self.root_memory, "count_summary.json")
        self.memory_vector_file = os.path.join(self.root_vector, "memory.index")

    def _ensure_memory_files(self):
        if not os.path.exists(self.memory_file):
            self.fm.write_json(self.memory_file, [])

        if not os.path.exists(self.summary_file):
            self.fm.write_json(self.summary_file, [])

        if not os.path.exists(self.count_summary_file):
            self.fm.write_json(self.count_summary_file, [])

        return True

    def format_str(self, data: list[dict]) -> str:
        conversation_blocks = []
        for record in data:
            parts = []

            parts.append(f"Time: {record.get('timestamp', get_current_time())}")
            parts.append(f"User: {record.get('user')}")

            if record.get("actions"):
                for actions in record.get("actions", []):
                    parts.append(
                        f"Action Call: {actions['name']}({actions['arguments']})"
                    )
                    parts.append(f"Action Out: {actions['output']}")

            parts.append(f"Assistant: {record.get('assistant')}")
            block = "\n".join(parts)
            conversation_blocks.append(block)

        return "\n\n".join(conversation_blocks)

    def save_memory(self, messages: list[dict]):
        self._ensure_memory_files()

        conversations = []
        actions = {}
        current = {
            "chat_id": generate_id("msg"),
            "timestamp": get_current_time(),
            "user": None,
            "actions": [],
            "assistant": None,
        }

        for item in messages:
            if item.get("role") == "user":
                if current["user"] or current["assistant"] or current["actions"]:
                    conversations.append(current)
                    current = {
                        "chat_id": generate_id("msg"),
                        "timestamp": get_current_time(),
                        "user": None,
                        "actions": [],
                        "assistant": None,
                    }
                current["user"] = item["content"]

            elif item.get("type") == "function_call":
                actions[item["call_id"]] = {
                    "type": item["type"],
                    "call_id": item["call_id"],
                    "name": item["name"],
                    "arguments": item["arguments"],
                }

            elif item.get("type") == "function_call_output":
                if item["call_id"] in actions:
                    actions[item["call_id"]]["output"] = item["output"]
                    # langsung masukkan ke current action
                    current["actions"].append(actions[item["call_id"]])
                    del actions[item["call_id"]]

            elif item.get("role") == "assistant":
                current["assistant"] = item["content"]

        if current["user"] or current["assistant"] or current["actions"]:
            conversations.append(current)

        self.memory_file = os.path.join(self.root_memory, "memory.json")
        self.fm.append_json(self.memory_file, conversations)

        if current["user"] and current.get("chat_id"):
            self.memory_vector_file = os.path.join(self.root_vector, "memory.index")
            self.vm.add_vector(current["user"], current, self.memory_vector_file)

    def load_memory(self, last_n: int = None) -> list:
        if not os.path.exists(self.memory_file):
            log.warning(f"Memory file '{self.memory_file}' does not exist.")
            return []

        data = self.fm.read_json(self.memory_file)

        if not isinstance(data, list):
            log.error("Memory file content is invalid (expected list).")
            return []

        if isinstance(last_n, int):
            return data[-last_n:]

        return data

    def filter_memory(
        self, data: list[dict], max_tokens: int = 1000, sort_by_score=False
    ):
        if not data:
            return []

        records = data.copy()

        # Urutkan berdasarkan score kalau diminta
        if sort_by_score:
            records.sort(key=lambda x: x.get("score", 0), reverse=True)

        def total_tokens(items):
            return token_count(self.format_str(items))

        # Trim token
        while total_tokens(records) > max_tokens:
            if len(records) <= 1:
                break  # minimal pertahankan 1
            records.pop(-1)  # buang skor terendah

        return records

    def load_all_memory(self) -> list:
        """Memuat seluruh riwayat chat yang tersimpan (TANPA filter)"""
        if not os.path.exists(self.memory_file):
            log.warning(f"Memory file '{self.memory_file}' does not exist.")
            return []

        data = self.fm.read_json(self.memory_file)

        if not isinstance(data, list):
            log.error("Memory file content is invalid (expected list).")
            return []

        return data
