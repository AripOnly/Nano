# # app/core/orchestrator.py

from app.utils import log, token_count
from app.agent import Agent
from app.services.model_openai import ModelOpenAI
from app.tools.tools_calling import ToolsCalling
from app.memory.recent_memory import RecentMemory
from app.memory.relevant_memory import RelevantMemory
from app.memory.summary_memory import SummaryMemory


class Orchestrator:
    def __init__(self):
        self.tools_mgr = ToolsCalling()

        # Init memory sekali saja
        self.summary = SummaryMemory(top_k=3, max_tokens=1024, min_score=0.3)
        self.relevant = RelevantMemory(
            top_k=5, last_n=10, min_score=0.3, max_tokens=1024
        )
        self.recent = RecentMemory(last_n=10, max_tokens=2048)

        # Model cukup init sekali
        self.model = ModelOpenAI("gpt-5-mini")

    def process_message(self, prompt, session_id="default"):
        messages = []

        personality = "Your name is Nano. You are an advanced AI assistant designed to assist users."
        messages.append({"role": "system", "content": personality})

        # Use existing instances
        summary_data = self.summary.get_summary_memory(prompt)
        if summary_data:
            log.info(f"Summary Memory Token Count: {token_count(summary_data)}")
            messages.append(
                {"role": "system", "content": f"Summary context:\n{summary_data}"}
            )

        relevant_data = self.relevant.get_relevant_memory(prompt)
        if relevant_data:
            log.info(f"Relevant Memory Token Count: {token_count(relevant_data)}")
            messages.append(
                {"role": "system", "content": f"Relevant context:\n{relevant_data}"}
            )

        recent_data = self.recent.get_recent_memory()
        log.info(f"Recent Memory Token Count: {token_count(recent_data)}")
        if recent_data:
            messages.append(
                {"role": "system", "content": f"Recent context:\n{recent_data}"}
            )

        messages.append({"role": "user", "content": prompt})

        agent = Agent(
            model=self.model, messages=messages, tools=self.tools_mgr.tools_schema()
        )
        return agent.run()
