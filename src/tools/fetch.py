import httpx
import trafilatura

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"
}
_TIMEOUT = 10
_MIN_CHARS = 200


def fetch_url(url: str, max_chars: int = 4000) -> str:
    """Fetch a URL and extract clean article text via trafilatura.

    Falls back to empty string on error or paywalled/JS-only pages.
    When extracted text is shorter than _MIN_CHARS the caller should
    rely on the search snippet instead.
    """
    try:
        response = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
        text = trafilatura.extract(response.text) or ""
        return text[:max_chars]
    except Exception:
        return ""
