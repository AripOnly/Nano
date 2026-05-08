# Nano AI Agent Framework

Nano is a modular AI Agent framework built with Python.  
This project is currently in the **prototype stage** and uses a **Single-Agent Architecture** with memory, RAG, and tool-calling capabilities.

---

## Features

- Modular AI Agent
- Single-Agent Architecture
- RAG Memory System
- Vector Search
- Tool Calling
- Summarization Memory
- Safe File Operations
- CLI Interface

---

## Current Status

⚠️ This project is still under active development and considered a prototype.

Some features may:
- still contain bugs
- change significantly
- be experimental
- not yet optimized for production use

---

## Tech Stack

- Python
- OpenAI API
- FAISS
- Sentence Transformers

---

## Architecture

Current architecture:
- Single Agent
- Memory-based Context Retrieval
- Vector Search using FAISS
- Tool Calling System
- File Management System
- Summarization Memory

Planned future architecture:
- Multi-Agent System
- Worker Agents
- Critic/Evaluator Agent
- Shared Memory System
- Autonomous Task Planning

---

## How to Run

```bash
pip install -r requirements.txt
python cli.py
