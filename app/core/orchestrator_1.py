# app/core/orchestrator.py

from app.utils import log
from app.agent import Agent
from app.services.model_openai import ModelOpenAI
from app.tools.tools_calling import ToolsCalling
from app.memory.recent_memory import RecentMemory
from app.memory.relevant_memory import RelevantMemory
from app.memory.summary_memory import SummaryMemory


class Orchestrator_1:
    def __init__(self, agent_model_name="gpt-5-mini"):
        # Tools
        self.tools_mgr = ToolsCalling()
        self.tools_schema = self.tools_mgr.tools_schema()

        # Memories
        self.summary_memory = SummaryMemory(top_k=3, max_tokens=1024, min_score=0.3)
        self.relevant_memory = RelevantMemory(
            top_k=5, last_n=10, min_score=0.3, max_tokens=1024
        )
        self.recent_memory = RecentMemory(last_n=20, max_tokens=1024)

        # Agent model
        self.agent_model_name = agent_model_name

    def _build_system_messages(self, prompt: str) -> list[dict]:
        """
        Build system messages for memory + personality
        """
        messages = []

        # Personality
        personality = (
            "Your name is Nano. You are an advanced AI assistant "
            "designed to assist users with a variety of tasks."
        )
        messages.append({"role": "system", "content": personality})

        # Memories
        summary_items = self.summary_memory.get_summary_memory(prompt=prompt)
        if summary_items:
            messages.append(
                {"role": "system", "content": f"Summary context:\n{summary_items}"}
            )
            log.info(f"Summary memory: {len(summary_items)} items found.")

        relevant_items = self.relevant_memory.get_relevant_memory(prompt=prompt)
        if relevant_items:
            messages.append(
                {"role": "system", "content": f"Relevant context:\n{relevant_items}"}
            )
            log.info(f"Relevant memory: {len(relevant_items)} items found.")

        recent_items = self.recent_memory.get_recent_memory()
        if recent_items:
            messages.append(
                {"role": "system", "content": f"Recent context:\n{recent_items}"}
            )
            log.info(f"Recent memory: {len(recent_items)} items found.")

        return messages

    def _run_agent(self, prompt: str) -> str:
        """
        Run a single agent with prompt and memories
        """
        messages = self._build_system_messages(prompt)
        messages.append({"role": "user", "content": prompt})

        model = ModelOpenAI(self.agent_model_name)
        agent = Agent(model=model, messages=messages, tools=self.tools_schema)

        try:
            return agent.run() or ""
        except Exception as e:
            log.warning(f"Agent failed: {e}")
            return f"[Agent Error]: {e}"

    def _choose_best_answer(self, answers: list[str]) -> str:
        """
        Use an AI model to select the best answer from multiple agent results
        """
        if len(answers) == 1:
            return answers[0]

        instructions = (
            "You are an evaluator AI. "
            "Given multiple answers from different agents, choose the best one. "
            "Return only the chosen answer."
        )
        model_chat = ModelOpenAI(model=self.agent_model_name, instructions=instructions)

        response = model_chat.call(
            messages=[
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": "Here are the agent answers:\n"
                    + "\n---\n".join(answers),
                },
            ]
        )
        output = response.get("output")
        return output.strip() if output else "[No answer selected]"

    def process(self, prompt: str, agents_count: int = 1) -> str:
        """
        Run multiple agents (sequentially) and select the best answer
        """
        results = [self._run_agent(prompt) for _ in range(agents_count)]
        log.info(f"Collected {len(results)} agent results.")
        return self._choose_best_answer(results)
