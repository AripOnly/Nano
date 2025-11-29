# app/agent/agent.py

import json
from app.services.model_openai import ModelOpenAI
from app.tools.tools_calling import ToolsCalling
from app.utils import clean_openai_output
from app.memory.base_memory import BaseMemory
from app.memory.base_summarizer import BaseSummarizer


class Agent:
    def __init__(
        self,
        model: ModelOpenAI | None = None,
        messages: list[dict] | None = None,
        tools: list[dict] | None = None,
        summary_cycle: int = 2,
    ):
        self.model = model
        self.messages = messages or []
        self.tools = tools or []
        self.tools_mgr = ToolsCalling()
        self.memory = BaseMemory()
        self.summary = BaseSummarizer()
        self.summary_cycle = summary_cycle

    def run(self):
        """
        Jalankan reasoning loop.
        input → pesan awal (default: self.messages)
        tools → daftar tools (default: self.tools)
        """
        message_input = self.messages
        tools = self.tools
        while True:
            try:
                response = self.model.call(messages=message_input, tools=tools)
            except Exception as e:
                return f"[Agent Error]: {e}"

            for item in getattr(response, "output", []):
                if getattr(item, "type", None) == "reasoning" and getattr(
                    item, "summary", None
                ):
                    for summary in item.summary:
                        print(f"\n[Reasoning]\n{summary.text}\n")

            clean_response = clean_openai_output(response.output)
            message_input += clean_response

            function_calls = [
                item
                for item in getattr(response, "output", [])
                if getattr(item, "type", None) == "function_call"
            ]

            if not function_calls:
                self.memory.save_memory(message_input)
                count = self.summary.get_counter()
                if count == self.summary_cycle:
                    for item in message_input:
                        if item.get("role") == "user":
                            prompt = item.get("content", "")
                            break

                    memory_data = self.memory.load_memory(self.summary_cycle)
                    memory_str = self.memory.format_str(memory_data)
                    self.summary.create_summary(prompt, memory_str)
                    self.summary.reset_counter()
                else:
                    self.summary.increment_counter()
                return getattr(response, "output_text", None)

            # Eksekusi function call
            for item in function_calls:
                tool_output = self.tools_mgr.tools_calling(
                    item.name, json.loads(item.arguments)
                )

                tool_attr = {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(tool_output, ensure_ascii=False),
                }
                message_input.append(tool_attr)
