import os

# Override via OPENROUTER_MODEL env var without touching code.
# Find current free models at: https://openrouter.ai/models?q=free
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

MAX_RETRIES = 2
MAX_SUBTASKS = 4
SEARCH_RESULTS_PER_QUERY = 5
URLS_TO_FETCH_PER_QUERY = 2
