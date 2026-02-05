"""
NewsAPI Tool - Get latest news articles
"""
import os
import httpx
from typing import Dict, Any
from datetime import datetime, timedelta


class NewsTool:
    """Tool for interacting with NewsAPI"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY environment variable is required")
        
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_top_headlines(
        self,
        query: str = None,
        category: str = None,
        country: str = "us",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get top headlines
        
        Args:
            query: Search query
            category: Category (business, entertainment, general, health, science, sports, technology)
            country: Country code (us, gb, ca, etc.)
            limit: Number of articles to return
            
        Returns:
            Dict with news articles
        """
        try:
            url = f"{self.BASE_URL}/top-headlines"
            params = {
                "apiKey": self.api_key,
                "pageSize": limit
            }
            
            if query:
                params["q"] = query
            if category:
                params["category"] = category
            if country and not query:  # Country doesn't work with query
                params["country"] = country
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format articles
            articles = []
            for article in data.get("articles", [])[:limit]:
                articles.append({
                    "title": article["title"],
                    "description": article["description"],
                    "source": article["source"]["name"],
                    "author": article.get("author"),
                    "published_at": article["publishedAt"],
                    "url": article["url"]
                })
            
            result = {
                "success": True,
                "total_results": data.get("totalResults", 0),
                "query": query,
                "articles": articles
            }
            
            # If no results and only country was specified, suggest using search_news instead
            if result["total_results"] == 0 and not query and country:
                result["suggestion"] = (
                    f"No headlines found for country '{country}'. "
                    f"Try using search_news with a specific query about the country instead."
                )
            
            return result
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"News API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def search_news(
        self,
        query: str,
        from_date: str = None,
        language: str = "en",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for news articles
        
        Args:
            query: Search query
            from_date: Start date (YYYY-MM-DD format)
            language: Language code (en, es, fr, etc.)
            limit: Number of articles to return
            
        Returns:
            Dict with news articles
        """
        try:
            url = f"{self.BASE_URL}/everything"
            
            # Default to last 7 days if no date specified
            if not from_date:
                from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            params = {
                "apiKey": self.api_key,
                "q": query,
                "from": from_date,
                "language": language,
                "sortBy": "relevancy",
                "pageSize": limit
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format articles
            articles = []
            for article in data.get("articles", [])[:limit]:
                articles.append({
                    "title": article["title"],
                    "description": article["description"],
                    "source": article["source"]["name"],
                    "author": article.get("author"),
                    "published_at": article["publishedAt"],
                    "url": article["url"]
                })
            
            return {
                "success": True,
                "total_results": data["totalResults"],
                "query": query,
                "articles": articles
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"News API error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
