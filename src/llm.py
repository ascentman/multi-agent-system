import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from src.config import MODEL_NAME

load_dotenv()


def get_llm(temperature: float = 0.2) -> ChatGroq:
    return ChatGroq(
        model=MODEL_NAME,
        temperature=temperature,
        api_key=os.environ["GROQ_API_KEY"],
    )


def get_json_llm(temperature: float = 0.1) -> ChatGroq:
    """LLM configured for reliable JSON output (used by decompose + validate nodes)."""
    return ChatGroq(
        model=MODEL_NAME,
        temperature=temperature,
        api_key=os.environ["GROQ_API_KEY"],
        model_kwargs={"response_format": {"type": "json_object"}},
    )
