"""
GitHub API Tool - Search repositories, get stars, contributors
"""
import httpx
from typing import Dict, Any, List, Optional


class GitHubTool:
    """Tool for interacting with GitHub API"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=50.0)
    
    async def search_repositories(
        self,
        query: str,
        limit: int = 5,
        sort: str = "stars"
    ) -> Dict[str, Any]:
        """
        Search GitHub repositories
        
        Args:
            query: Search query (e.g., "machine learning python"). Cannot be empty.
                  For top repos, use "stars:>1000" or a specific topic/language.
            limit: Number of results to return
            sort: Sort by (stars, forks, updated)
            
        Returns:
            Dict with repository results
        """
        # Validate query is not empty
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Query parameter cannot be empty. For top repositories, use a query like 'stars:>1000' or specify a language/topic."
            }
        
        try:
            url = f"{self.BASE_URL}/search/repositories"
            params = {
                "q": query.strip(),
                "sort": sort,
                "order": "desc",
                "per_page": limit
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format results
            repos = []
            for item in data.get("items", [])[:limit]:
                repos.append({
                    "name": item["full_name"],
                    "description": item["description"],
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "language": item["language"],
                    "url": item["html_url"],
                    "topics": item.get("topics", [])
                })
            
            return {
                "success": True,
                "query": query,
                "total_count": data["total_count"],
                "repositories": repos
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"GitHub API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get details about a specific repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict with repository details
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "name": data["full_name"],
                "description": data["description"],
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "watchers": data["watchers_count"],
                "language": data["language"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "topics": data.get("topics", []),
                "url": data["html_url"]
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"GitHub API error: {str(e)}"
            }
    
    async def get_contributors(
        self,
        owner: str,
        repo: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get top contributors for a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            limit: Number of contributors to return
            
        Returns:
            Dict with contributor information
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
            params = {"per_page": limit}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            contributors = []
            for contributor in data[:limit]:
                contributors.append({
                    "username": contributor["login"],
                    "contributions": contributor["contributions"],
                    "profile_url": contributor["html_url"]
                })
            
            return {
                "success": True,
                "repository": f"{owner}/{repo}",
                "contributors": contributors
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"GitHub API error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
