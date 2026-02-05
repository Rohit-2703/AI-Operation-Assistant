"""
OpenWeatherMap API Tool - Get current weather data
"""
import os
import httpx
from typing import Dict, Any
from .query_optimizer import QueryOptimizer
from .retry_utils import retry_api_call


class WeatherTool:
    """Tool for interacting with OpenWeatherMap API"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHERMAP_API_KEY environment variable is required")
        
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry_api_call(max_attempts=3)
    async def _fetch_weather_data(self, city: str, units: str) -> Dict[str, Any]:
        """
        Internal method to fetch weather data with retry logic
        This method is retried automatically on transient errors
        """
        url = f"{self.BASE_URL}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_current_weather(
        self,
        city: str,
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Get current weather for a city
        
        Args:
            city: City name (e.g., "London", "New York")
            units: Units (metric, imperial, standard)
            
        Returns:
            Dict with weather information
        """
        # Use AI-powered query optimization with city context
        original_city = city
        corrected_city, correction_note = await QueryOptimizer.correct_query(city, context="city")
        
        try:
            # This call will be retried automatically on transient errors
            data = await self._fetch_weather_data(corrected_city, units)
            
            # Format response
            temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
            
            result = {
                "success": True,
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": f"{data['main']['temp']}{temp_unit}",
                "feels_like": f"{data['main']['feels_like']}{temp_unit}",
                "humidity": f"{data['main']['humidity']}%",
                "description": data["weather"][0]["description"],
                "wind_speed": f"{data['wind']['speed']} m/s",
                "coordinates": {
                    "lat": data["coord"]["lat"],
                    "lon": data["coord"]["lon"]
                }
            }
            
            # Add correction note if city was corrected
            if correction_note:
                result["correction_note"] = correction_note
            
            return result
            
        except httpx.HTTPStatusError as e:
            # After retries exhausted, handle final errors
            if e.response.status_code == 404:
                # Generate helpful error message
                error_reason = QueryOptimizer.get_error_reason("weather", original_city, "City not found")
                return {
                    "success": False,
                    "error": error_reason
                }
            return {
                "success": False,
                "error": f"Weather API error: {str(e)}"
            }
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # Network errors that couldn't be recovered after retries
            return {
                "success": False,
                "error": f"Network error: {str(e)}. Please check your connection."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    @retry_api_call(max_attempts=3)
    async def _fetch_forecast_data(self, city: str, units: str, days: int) -> Dict[str, Any]:
        """
        Internal method to fetch forecast data with retry logic
        This method is retried automatically on transient errors
        """
        url = f"{self.BASE_URL}/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units,
            "cnt": min(days * 8, 40)
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status() 
        return response.json()
    
    async def get_forecast(
        self,
        city: str,
        days: int = 3,
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a city
        
        Args:
            city: City name
            days: Number of days (1-5)
            units: Units (metric, imperial, standard)
            
        Returns:
            Dict with forecast information
        """
        # Use AI-powered query optimization with city context
        original_city = city
        corrected_city, correction_note = await QueryOptimizer.correct_query(city, context="city")
        
        try:
            # This call will be retried automatically on transient errors
            data = await self._fetch_forecast_data(corrected_city, units, days)
            
            temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
            
            # Format forecast
            forecast_list = []
            for item in data["list"][:days * 8:8]:  # One per day
                forecast_list.append({
                    "date": item["dt_txt"],
                    "temperature": f"{item['main']['temp']}{temp_unit}",
                    "description": item["weather"][0]["description"],
                    "humidity": f"{item['main']['humidity']}%"
                })
            
            result = {
                "success": True,
                "city": data["city"]["name"],
                "country": data["city"]["country"],
                "forecast": forecast_list
            }
            
            # Add correction note if city was corrected
            if correction_note:
                result["correction_note"] = correction_note
            
            return result
            
        except httpx.HTTPStatusError as e:
            # After retries exhausted, handle final errors
            if e.response.status_code == 404:
                # Generate helpful error message
                error_reason = QueryOptimizer.get_error_reason("weather", original_city, "City not found")
                return {
                    "success": False,
                    "error": error_reason
                }
            return {
                "success": False,
                "error": f"Weather API error: {str(e)}"
            }
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # Network errors that couldn't be recovered after retries
            return {
                "success": False,
                "error": f"Network error: {str(e)}. Please check your connection."
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"Weather API error: {str(e)}"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
