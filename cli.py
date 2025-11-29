# cli.py

from app.config import config
from app.core.orchestrator import Orchestrator
from app.utils.logger import log

log.info("APP Start...")
engine = Orchestrator()

while True:
    print("=========================== Nano V1 ===========================")

    user_input = input("Mas Arip: ")

    if user_input.lower() in ["exit", "quit"]:
        log.info("APP Shutdown...")
        break

    response = engine.process(user_input)
    print(f"\nNano: {response}\n")
