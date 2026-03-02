import httpx
from typing import List, Dict
from config import TAVILY_API_KEY


class WebSearchError(RuntimeError):
    pass


async def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    if not TAVILY_API_KEY:
        raise WebSearchError("TAVILY_API_KEY is not set")

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        data = r.json()

    results = data.get("results", [])
    out = []
    for item in results[:max_results]:
        out.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
        )
    return out


def format_results(results: List[Dict[str, str]]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        snippet = (r.get("snippet", "") or "").strip().replace("\n", " ")
        lines.append(f"{i}. {title}\n{url}\n{snippet}")
    return "\n\n".join(lines)