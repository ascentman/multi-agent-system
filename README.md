---
title: Multi-Agent Competitive Research
emoji: 🔎
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
---

# Multi-Agent Competitive Research Tool

A **learning-first** multi-agent system that produces a competitive intelligence briefing for any company. Built with LangGraph + OpenRouter (free tier) + Gradio.

## Architecture

```
User Input: "Acme Corp"
        │
        ▼
┌─────────────────┐
│  Planner Agent  │  ← decomposes request into 3-4 research subtasks
└────────┬────────┘
         │  subtask loop
         ▼
┌─────────────────┐
│ Researcher Agent│  ← web search + URL fetch + LLM summarization
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Planner Validate│  ← are the notes on-topic and useful?
└────────┬────────┘
    ┌────┴────┐
  valid    invalid (retry up to 2×)
    │         └──► refine query → Researcher
    ▼
┌─────────────────┐
│  Synthesizer    │  ← aggregates all validated notes → markdown report
└─────────────────┘
```

Every step is streamed live to the UI so you can watch each agent think.

## Tech Stack

| Tool | Purpose | Cost |
|------|---------|------|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Multi-agent orchestration | Free |
| [OpenRouter](https://openrouter.ai) | LLM API (`google/gemma-4-31b-it:free`) | Free |
| [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) | Web search, no API key | Free |
| [trafilatura](https://trafilatura.readthedocs.io) | Clean article extraction | Free |
| [Gradio](https://gradio.app) | Web UI + streaming | Free |
| [HF Spaces](https://huggingface.co/spaces) | Hosting | Free |

## Local Setup

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd multi-agent-system

# 2. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key (get yours free at https://openrouter.ai — no card required)
cp .env.example .env
# Edit .env and paste your OPENROUTER_API_KEY

# 5. Run
python app.py
# Open http://127.0.0.1:7860
```

## Running Tests

```bash
pytest tests/ -v
```

## What You'll Learn

See [LEARNING_NOTES.md](LEARNING_NOTES.md) for a concept-by-concept walkthrough explaining *why* each design choice was made.

## Deployment (Hugging Face Spaces)

1. Create a Space at huggingface.co/spaces with **SDK = Gradio**
2. Add `OPENROUTER_API_KEY` in Space Settings → Secrets
3. Push this repo to the Space's git remote
