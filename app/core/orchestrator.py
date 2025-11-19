# # app/core/orchestrator.py

from app.utils import log
from app.agent import Agent
from app.services.model_openai import ModelOpenAI
from app.tools.tools_calling import ToolsCalling
from app.memory.recent_memory import RecentMemory
from app.memory.relevant_memory import RelevantMemory
from app.memory.summary_memory import SummaryMemory


class Orchestrator:
    def __init__(self):
        self.tools_mgr = ToolsCalling()

    def process(self, prompt):
        messages = []

        personality = "Your name is Nano. You are an advanced AI assistant designed to assist users with a variety of tasks."
        messages.append({"role": "system", "content": personality})

        summary = SummaryMemory(top_k=3, max_tokens=1024, min_score=0.3)
        summary = summary.get_summary_memory(prompt=prompt)
        log.info(f"Summary memory: {len(summary)} items found.")
        if summary:
            messages.append(
                {"role": "system", "content": f"Summary context:\n{summary}"}
            )
        relevant = RelevantMemory(top_k=5, last_n=10, min_score=0.3, max_tokens=1024)
        relevant = relevant.get_relevant_memory(prompt=prompt)
        log.info(f"Relevant memory: {len(relevant)} items found.")
        if relevant:
            messages.append(
                {"role": "system", "content": f"Relevant context:\n{relevant}"}
            )

        recent = RecentMemory(last_n=20, max_tokens=1024)
        recent = recent.get_recent_memory()
        log.info(f"Recent memory: {len(recent)} items found.")
        if recent:
            messages.append({"role": "system", "content": f"Recent context:\n{recent}"})

        messages.append({"role": "user", "content": prompt})

        model = ModelOpenAI("gpt-5-mini")
        agent = Agent(
            model=model, messages=messages, tools=self.tools_mgr.tools_schema()
        )
        result = agent.run()
        return result
