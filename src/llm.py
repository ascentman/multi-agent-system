import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from src.config import MODEL_NAME

load_dotenv()

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=temperature,
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url=_OPENROUTER_BASE,
    )


def get_json_llm(temperature: float = 0.1) -> ChatOpenAI:
    """Same model, lower temperature — JSON enforcement is prompt-only for OpenRouter free models."""
    return get_llm(temperature=temperature)
