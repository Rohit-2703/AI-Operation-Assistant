"""
REST Countries API Tool - Get country information
"""
import httpx
from typing import Dict, Any, List
from .query_optimizer import QueryOptimizer


class CountriesTool:
    """Tool for interacting with REST Countries API"""
    
    BASE_URL = "https://restcountries.com/v3.1"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_country_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get country information by name
        
        Args:
            name: Country name (full or partial)
            
        Returns:
            Dict with country information
        """
        # Use AI-powered query optimization with general context for country names
        original_name = name
        corrected_name, correction_note = await QueryOptimizer.correct_query(name, context="general")
        
        try:
            url = f"{self.BASE_URL}/name/{corrected_name}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Get first match
            country = data[0]
            
            result = {
                "success": True,
                "name": country["name"]["common"],
                "official_name": country["name"]["official"],
                "capital": country.get("capital", ["N/A"])[0],
                "region": country["region"],
                "subregion": country.get("subregion", "N/A"),
                "population": country["population"],
                "area": f"{country['area']} km²",
                "languages": list(country.get("languages", {}).values()),
                "currencies": list(country.get("currencies", {}).keys()),
                "timezones": country.get("timezones", []),
                "flag": country["flag"]
            }
            
            # Add correction note if country name was corrected
            if correction_note:
                result["correction_note"] = correction_note
            
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Country '{original_name}' not found. Please check the spelling."
                }
            return {
                "success": False,
                "error": f"Countries API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def get_countries_by_region(self, region: str) -> Dict[str, Any]:
        """
        Get all countries in a region
        
        Args:
            region: Region name (Africa, Americas, Asia, Europe, Oceania)
            
        Returns:
            Dict with list of countries
        """
        try:
            url = f"{self.BASE_URL}/region/{region}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            countries = []
            for country in data:
                countries.append({
                    "name": country["name"]["common"],
                    "capital": country.get("capital", ["N/A"])[0],
                    "population": country["population"],
                    "flag": country["flag"]
                })
            
            # Sort by population
            countries.sort(key=lambda x: x["population"], reverse=True)
            
            return {
                "success": True,
                "region": region,
                "count": len(countries),
                "countries": countries
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Countries API error: {str(e)}"
            }
    
    async def get_country_by_code(self, code: str) -> Dict[str, Any]:
        """
        Get country by ISO code
        
        Args:
            code: ISO country code (e.g., US, GB, IN)
            
        Returns:
            Dict with country information
        """
        try:
            url = f"{self.BASE_URL}/alpha/{code}"
            response = await self.client.get(url)
            response.raise_for_status()
            
            country = response.json()
            
            return {
                "success": True,
                "name": country["name"]["common"],
                "official_name": country["name"]["official"],
                "capital": country.get("capital", ["N/A"])[0],
                "region": country["region"],
                "population": country["population"],
                "area": f"{country['area']} km²",
                "flag": country["flag"]
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Countries API error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
