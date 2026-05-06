from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo text search. Returns list of {title, href, body} dicts."""
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []
