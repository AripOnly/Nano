# app/config/config.py

import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # Setting logging
    LOG_ENABLED = True

    # API keys & sensitive data
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Model configs
    MODEL_MAIN = "gpt-5-mini"
    MODEL_INTENT_CLASSIFIER = "gpt-5-mini"
    MODEL_SUMMARY = "gpt-5-mini"
    MODEL_EMBEDDING = "all-MiniLM-L6-v2"
    MODEL_ANALYZE_IMAGE = "gpt-5-mini"
    MODEL_GENERATE_IMAGE = "gpt-5-mini"

    # Token Limit
    MAX_HISTORY = 10
    HISTORY_TOKEN_LIMIT = 2000

    MAX_RECALL_HISTORY = 5
    RECALL_HISTORY_TOKEN_LIMIT = 1500
    MIN_SCORE_HISTORY = 0.3

    MAX_RECALL_SUMMARY = 5
    RECALL_SUMMARY_TOKEN_LIMIT = 1000
    MIN_SCORE_SUMMARY = 0.3
    SUMMARY_INTERVAL = 2

    # Path data
    MEMORY_ROOT = "app/data/memory/"
    VECTOR_ROOT = "app/data/vector_store/"
    FILES_ROOT = "app/data/files/"
