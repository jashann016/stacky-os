import httpx
import urllib.parse
from typing import Dict, Any, List

async def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Query DuckDuckGo Instant Answer and HTML search for live web intelligence."""
    try:
        encoded_query = urllib.parse.quote_plus(query)
        # Using DuckDuckGo Lite API
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            data = resp.json()
            
            results = []
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", "Overview"),
                    "snippet": data.get("AbstractText"),
                    "source": data.get("AbstractURL", "")
                })
            
            # Related Topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if "Text" in topic:
                    results.append({
                        "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                        "snippet": topic.get("Text", ""),
                        "source": topic.get("FirstURL", "")
                    })
            
            if not results:
                # Direct summary fallback
                return [{"title": query, "snippet": f"No direct encyclopedia summary found for '{query}', query dispatched.", "source": "DuckDuckGo"}]
            return results
    except Exception as e:
        return [{"error": f"Search encountered an anomaly: {str(e)}"}]
