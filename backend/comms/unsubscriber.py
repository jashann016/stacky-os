import re
import httpx
from typing import List, Dict, Any

class EmailUnsubscriber:
    """Detects and navigates unsubscribe headers and links in marketing emails."""
    
    @staticmethod
    def extract_unsubscribe_links(email_body: str, email_headers: Dict[str, str] = None) -> List[str]:
        links = []
        if email_headers and "List-Unsubscribe" in email_headers:
            raw_hdr = email_headers["List-Unsubscribe"]
            matches = re.findall(r'<https?://[^>]+>', raw_hdr)
            links.extend([m.strip('<>') for m in matches])
        
        # Regex search in body
        found_in_body = re.findall(r'href=[\'"](https?://[^\'">]*unsubscribe[^\'">]*)[\'"]', email_body, re.IGNORECASE)
        links.extend(found_in_body)
        return list(set(links))

    @staticmethod
    async def auto_unsubscribe(url: str) -> Dict[str, Any]:
        """Perform automated HTTP trigger to execute unsubscription safely."""
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                res = await client.get(url)
                return {
                    "url": url,
                    "status_code": res.status_code,
                    "success": res.status_code in [200, 202, 204],
                    "message": "Unsubscribe request delivered successfully."
                }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
