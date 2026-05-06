import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from dotenv import load_dotenv
from openai import RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import MODEL_NAME

load_dotenv()

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=temperature,
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url=_OPENROUTER_BASE,
        max_retries=0,  # we handle retries ourselves via call_llm
    )


def get_json_llm(temperature: float = 0.1) -> ChatOpenAI:
    """Same model, lower temperature — JSON enforcement is prompt-only for free models."""
    return get_llm(temperature=temperature)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(8),
    reraise=True,
)
def call_llm(llm: ChatOpenAI, messages: list[BaseMessage]) -> str:
    """Invoke the LLM and return content string. Retries on 429 with exponential backoff (5s→10s→20s…60s)."""
    return llm.invoke(messages).content
