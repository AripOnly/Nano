# app/services/openai_service.py

import os
from dotenv import load_dotenv
from openai import OpenAI
from app.utils import log


class ModelOpenAI:
    """
    Service untuk koneksi dan pemanggilan model OpenAI.
    - GPT-4o → hanya mendukung temperature
    - GPT-5  → hanya mendukung reasoning (termasuk gpt-5-mini & gpt-5-nano)
    """

    def __init__(self, model: str):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            log.error("OPENAI_API_KEY tidak ditemukan di environment variables.")
            raise ValueError("OPENAI_API_KEY tidak ditemukan di environment variables.")

        self.client = OpenAI(api_key=api_key)
        self.model = model.lower()
        self.instructions = None
        self.reasoning = {"effort": "medium", "summary": "auto"}
        self.text = {"verbosity": "medium"}
        self.temperature = 0.7
        self.max_tokens = 4096
        self.top_p = 1.0
        self.stop = None
        self.metadata = {}
        self.parallel_tool_calls = True

    def update_config(self, **kwargs):
        """
        Update konfigurasi model secara dinamis.
        Contoh:
            gpt.update_config(temperature=0.3, top_p=0.9, timeout=15)
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                log.debug(f"Config updated: {key}={value}")
            else:
                log.warning(f"Config '{key}' tidak dikenal dan diabaikan.")

        log.info("Konfigurasi model diperbarui.")

    def call(self, messages: list[dict], tools: list[dict] = None):
        """
        Panggil model sesuai konfigurasi yang aktif.
        """
        try:
            params = {
                "model": self.model,
                "input": messages,
                "instructions": self.instructions,
                "tools": tools or [],
                "tool_choice": "auto",
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
                "metadata": self.metadata,
                "parallel_tool_calls": self.parallel_tool_calls,
            }

            if self.stop:
                params["stop"] = self.stop

            if any(
                tag in self.model
                for tag in ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gtp-5.1"]
            ):
                params["reasoning"] = self.reasoning
                params["text"] = self.text
            elif any(tag in self.model for tag in ["gpt-4o", "gpt-4o-mini"]):
                params["temperature"] = self.temperature

            response = self.client.responses.create(**params)
            log.info(
                f"model: {self.model}, length messages: {len(messages)}, tools: {len(tools) if tools else 0}"
            )
            return response

        except Exception as e:
            log.error(f"Error panggil {self.model}: {str(e)}")
            return {"status": "error", "message": str(e)}
