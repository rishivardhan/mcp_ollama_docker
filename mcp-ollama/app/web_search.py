import re
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS

def needs_fresh_info(question: str) -> bool:
    """Check if a question likely needs fresh internet information."""
    fresh_keywords = [
        "latest", "current", "today", "new", "recent", "now",
        "version", "update", "price", "cost", "available",
        "release", "announcement", "change", "breaking"
    ]

    question_lower = question.lower()
    return any(keyword in question_lower for keyword in fresh_keywords)

async def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Search the web using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", "")
            })

        return {
            "success": True,
            "results": formatted_results,
            "query": query
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def summarize_web_results(results: List[Dict[str, str]]) -> str:
    """Summarize web search results for context."""
    if not results:
        return "No web results found."

    summary = "Recent web information:\n\n"
    for i, result in enumerate(results[:3], 1):  # Limit to top 3
        summary += f"{i}. {result['title']}\n"
        summary += f"   {result['snippet'][:200]}...\n"
        summary += f"   Source: {result['url']}\n\n"

    return summary