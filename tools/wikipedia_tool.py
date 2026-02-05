"""
Wikipedia API Tool - Search and get article summaries
"""
import httpx
from typing import Dict, Any


class WikipediaTool:
    """Tool for interacting with Wikipedia API"""
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"
    
    def __init__(self):
        headers = {
            "User-Agent": "AI-Operations-Assistant/1.0 (https://github.com/your-repo; contact@example.com)"
        }
        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)
    
    async def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search Wikipedia articles
        
        Args:
            query: Search query
            limit: Number of results to return
            
        Returns:
            Dict with search results
        """
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": query,
                "limit": limit,
                "format": "json"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format: [query, [titles], [descriptions], [urls]]
            results = []
            if len(data) >= 4:
                titles = data[1]
                descriptions = data[2]
                urls = data[3]
                
                for i in range(len(titles)):
                    results.append({
                        "title": titles[i],
                        "description": descriptions[i],
                        "url": urls[i]
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Wikipedia API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def get_summary(self, title: str) -> Dict[str, Any]:
        """
        Get summary of a Wikipedia article
        
        Args:
            title: Article title
            
        Returns:
            Dict with article summary
        """
        try:
            title_encoded = title.replace(" ", "_")
            url = f"{self.BASE_URL}/page/summary/{title_encoded}"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "title": data["title"],
                "extract": data["extract"],
                "url": data["content_urls"]["desktop"]["page"],
                "thumbnail": data.get("thumbnail", {}).get("source")
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Article '{title}' not found"
                }
            return {
                "success": False,
                "error": f"Wikipedia API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def get_article_html(self, title: str) -> Dict[str, Any]:
        """
        Get full HTML content of an article
        
        Args:
            title: Article title
            
        Returns:
            Dict with HTML content
        """
        try:
            title_encoded = title.replace(" ", "_")
            url = f"{self.BASE_URL}/page/html/{title_encoded}"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "title": title,
                "html": response.text[:1000] 
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Wikipedia API error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
