import time

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import SEARCH_RESULTS_PER_QUERY, URLS_TO_FETCH_PER_QUERY
from src.llm import get_llm
from src.prompts import RESEARCHER_SYSTEM, RESEARCHER_USER
from src.state import AgentState
from src.tools.fetch import fetch_url, _MIN_CHARS
from src.tools.search import web_search


def researcher(state: AgentState) -> dict:
    """Search the web, fetch top URLs, and summarize notes for the current subtask."""
    subtask = state["subtasks"][state["current_subtask_idx"]]
    query = state["current_query"]

    # 1. Web search
    results = web_search(query, max_results=SEARCH_RESULTS_PER_QUERY)

    # 2. Fetch top URLs; fall back to snippet when page text is too thin
    content_parts: list[str] = []
    fetched = 0
    for r in results:
        snippet = f"[{r.get('title', '')}] {r.get('body', '')}"
        if fetched < URLS_TO_FETCH_PER_QUERY:
            page_text = fetch_url(r.get("href", ""))
            if len(page_text) >= _MIN_CHARS:
                content_parts.append(f"Source: {r.get('href', '')}\n{page_text}")
                fetched += 1
            else:
                content_parts.append(snippet)
        else:
            content_parts.append(snippet)

    content = "\n\n---\n\n".join(content_parts) if content_parts else "No results found."

    # 3. LLM summarization
    llm = get_llm()
    messages = [
        SystemMessage(content=RESEARCHER_SYSTEM),
        HumanMessage(content=RESEARCHER_USER.format(subtask=subtask, content=content)),
    ]
    time.sleep(2)
    notes_text = llm.invoke(messages).content.strip()

    trace_msg = f"**Researcher:** Fetched {len(results)} results for `{query}`. Summarized notes."
    return {
        "pending_notes": notes_text,
        "trace": state.get("trace", []) + [trace_msg],
    }
