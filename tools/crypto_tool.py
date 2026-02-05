"""
CoinGecko API Tool - Get cryptocurrency prices and information
"""
import httpx
from typing import Dict, Any, List
from .query_optimizer import QueryOptimizer
from .retry_utils import retry_api_call


class CryptoTool:
    """Tool for interacting with CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry_api_call(max_attempts=3)
    async def _fetch_price_data(self, coin_id: str, vs_currency: str) -> Dict[str, Any]:
        """Internal method to fetch price data with retry logic"""
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_price(
        self,
        coin_id: str = "bitcoin",
        vs_currency: str = "usd"
    ) -> Dict[str, Any]:
        """
        Get current price of a cryptocurrency
        
        Args:
            coin_id: Coin ID (bitcoin, ethereum, cardano, etc.)
            vs_currency: Currency to compare (usd, eur, gbp, etc.)
            
        Returns:
            Dict with price information
        """
        # Use AI-powered query optimization with crypto context
        original_coin = coin_id
        corrected_coin, correction_note = await QueryOptimizer.correct_query(coin_id, context="crypto")
        
        try:
            # This call will be retried automatically on transient errors
            data = await self._fetch_price_data(corrected_coin, vs_currency)
            
            if corrected_coin not in data:
                # Generate helpful error message
                error_reason = QueryOptimizer.get_error_reason("crypto", original_coin, "Coin not found")
                return {
                    "success": False,
                    "error": error_reason
                }
            
            coin_data = data[corrected_coin]
            price_key = vs_currency
            
            result = {
                "success": True,
                "coin": corrected_coin,
                "currency": vs_currency.upper(),
                "price": coin_data[price_key],
                "market_cap": coin_data.get(f"{price_key}_market_cap"),
                "24h_volume": coin_data.get(f"{price_key}_24h_vol"),
                "24h_change": f"{coin_data.get(f'{price_key}_24h_change', 0):.2f}%"
            }
            
            # Add correction note if coin was corrected
            if correction_note:
                result["correction_note"] = correction_note
            
            return result
            
        except httpx.HTTPStatusError as e:
            # After retries exhausted, handle final errors
            error_reason = QueryOptimizer.get_error_reason("crypto", original_coin, str(e))
            return {
                "success": False,
                "error": error_reason
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
    async def _fetch_trending_data(self) -> Dict[str, Any]:
        """Internal method to fetch trending data with retry logic"""
        url = f"{self.BASE_URL}/search/trending"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def get_trending(self) -> Dict[str, Any]:
        """
        Get trending cryptocurrencies
        
        Returns:
            Dict with trending coins
        """
        try:
            # This call will be retried automatically on transient errors
            data = await self._fetch_trending_data()
            
            coins = []
            for item in data.get("coins", [])[:7]:
                coin = item["item"]
                coins.append({
                    "name": coin["name"],
                    "symbol": coin["symbol"],
                    "market_cap_rank": coin.get("market_cap_rank"),
                    "price_btc": coin.get("price_btc")
                })
            
            return {
                "success": True,
                "trending_coins": coins
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"CoinGecko API error: {str(e)}"
            }
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}. Please check your connection."
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"CoinGecko API error: {str(e)}"
            }
    
    @retry_api_call(max_attempts=3)
    async def _fetch_market_data(self, coin_id: str, vs_currency: str) -> Dict[str, Any]:
        """Internal method to fetch market data with retry logic"""
        url = f"{self.BASE_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_market_data(
        self,
        coin_id: str = "bitcoin",
        vs_currency: str = "usd"
    ) -> Dict[str, Any]:
        """
        Get detailed market data for a cryptocurrency
        
        Args:
            coin_id: Coin ID
            vs_currency: Currency to compare
            
        Returns:
            Dict with market data
        """
        # Use AI-powered query optimization with crypto context
        original_coin = coin_id
        corrected_coin, correction_note = await QueryOptimizer.correct_query(coin_id, context="crypto")
        
        try:
            # This call will be retried automatically on transient errors
            data = await self._fetch_market_data(corrected_coin, vs_currency)
            market_data = data["market_data"]
            
            result = {
                "success": True,
                "name": data["name"],
                "symbol": data["symbol"].upper(),
                "current_price": market_data["current_price"][vs_currency],
                "market_cap": market_data["market_cap"][vs_currency],
                "market_cap_rank": data["market_cap_rank"],
                "total_volume": market_data["total_volume"][vs_currency],
                "high_24h": market_data["high_24h"][vs_currency],
                "low_24h": market_data["low_24h"][vs_currency],
                "price_change_24h": market_data["price_change_24h"],
                "price_change_percentage_24h": f"{market_data['price_change_percentage_24h']:.2f}%",
                "circulating_supply": market_data.get("circulating_supply"),
                "total_supply": market_data.get("total_supply")
            }
            
            # Add correction note if coin was corrected
            if correction_note:
                result["correction_note"] = correction_note
            
            return result
            
        except httpx.HTTPStatusError as e:
            # After retries exhausted, handle final errors
            if e.response.status_code == 404:
                # Generate helpful error message
                error_reason = QueryOptimizer.get_error_reason("crypto", original_coin, "Coin not found")
                return {
                    "success": False,
                    "error": error_reason
                }
            error_reason = QueryOptimizer.get_error_reason("crypto", original_coin, str(e))
            return {
                "success": False,
                "error": error_reason
            }
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # Network errors that couldn't be recovered after retries
            return {
                "success": False,
                "error": f"Network error: {str(e)}. Please check your connection."
            }
        except httpx.HTTPError as e:
            error_reason = QueryOptimizer.get_error_reason("crypto", original_coin, str(e))
            return {
                "success": False,
                "error": error_reason
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
