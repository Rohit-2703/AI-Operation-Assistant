"""
AI-Powered Query Optimization Utility - Uses LLM to intelligently correct queries
"""
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependencies
_llm_client = None


def _get_llm_client():
    """Get LLM client singleton (lazy import)"""
    global _llm_client
    if _llm_client is None:
        from llm.client import get_llm_client
        _llm_client = get_llm_client()
    return _llm_client


class QueryOptimizer:
    """AI-powered query correction that uses LLM to intelligently correct any query type"""
    
    @staticmethod
    def is_likely_invalid(query: str, min_length: int = 3) -> bool:
        """
        Check if a query is likely invalid (not just a typo)
        
        Args:
            query: The query string
            min_length: Minimum reasonable length
            
        Returns:
            True if query seems invalid (random characters, too short, etc.)
        """
        if not query or len(query.strip()) < min_length:
            return True
        
        # Check for random character patterns (like XyzAbc123City)
        query_lower = query.lower().strip()
        
        # If it contains numbers mixed with letters in a weird pattern, likely invalid
        has_numbers = any(c.isdigit() for c in query)
        has_letters = any(c.isalpha() for c in query)
        
        # If it's very short with numbers, likely invalid
        if len(query) < 8 and has_numbers and has_letters:
            # Check if it looks like random characters
            if query_lower.count('xyz') > 0 or query_lower.count('abc') > 0:
                return True
        
        # If it's all numbers or mostly special characters, likely invalid
        if len([c for c in query if c.isalnum()]) < min_length:
            return True
        
        return False
    
    @staticmethod
    async def correct_query(query: str, context: str = "general") -> Tuple[str, Optional[str]]:
        """
        Use AI to intelligently correct any query - understands context and fixes typos/variations
        
        Args:
            query: The query string (potentially misspelled)
            context: Context hint (e.g., "city", "crypto", "tech", "general")
                    Helps AI understand what type of correction to make
            
        Returns:
            Tuple of (corrected_query, correction_note)
            correction_note is None if no correction was made
        """
        query = query.strip()
        
        # Check if likely invalid (random characters) - don't waste LLM call
        min_length = 2 if context == "crypto" else 3
        if QueryOptimizer.is_likely_invalid(query, min_length=min_length):
            return query, None
        
        try:
            llm_client = _get_llm_client()
            
            # Build context-aware system prompt
            context_guidance = {
                "city": "This is a city name. Correct to standard city spelling (e.g., 'Bengalore' → 'Bangalore', 'Londn' → 'London').",
                "crypto": "This is a cryptocurrency name. Correct to standard CoinGecko ID format (e.g., 'btc' → 'bitcoin', 'btcoin' → 'bitcoin').",
                "tech": "This is a tech term. Normalize to standard form (e.g., 'reactjs' → 'react', 'nodejs' → 'node').",
                "general": "This could be any type of query. Intelligently correct typos and variations based on common patterns."
            }
            
            context_hint = context_guidance.get(context, context_guidance["general"])
            
            system_prompt = f"""You are an intelligent query correction assistant. Your job is to correct misspelled or non-standard queries to their proper, commonly recognized form.

            Context: {context_hint}

            Rules:
            1. If the input is a valid query (even if slightly misspelled), correct it to the standard spelling/format
            2. Handle common typos, abbreviations, and variations intelligently
            3. If the input is clearly invalid (random characters, gibberish), return the original unchanged
            4. Be smart about context - understand what the user likely meant
            5. Return ONLY a JSON object with "corrected" (the corrected query) and "note" (brief explanation, or null if no correction needed)

            Examples:
            - City: "Bengalore" → {{"corrected": "Bangalore", "note": "Corrected 'Bengalore' to 'Bangalore'"}}
            - City: "Londn" → {{"corrected": "London", "note": "Corrected 'Londn' to 'London'"}}
            - Crypto: "btc" → {{"corrected": "bitcoin", "note": "Corrected 'btc' to 'bitcoin'"}}
            - Crypto: "btcoin" → {{"corrected": "bitcoin", "note": "Corrected 'btcoin' to 'bitcoin'"}}
            - Tech: "reactjs" → {{"corrected": "react", "note": "Corrected 'reactjs' to 'react'"}}
            - Invalid: "XyzAbc123City" → {{"corrected": "XyzAbc123City", "note": null}}
            - Already correct: "Tokyo" → {{"corrected": "Tokyo", "note": null}}"""

            user_prompt = f"Correct this query if it's misspelled or non-standard: {query}"
            
            result = await llm_client.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,  # Low temperature for consistency
                max_tokens=150
            )
            
            corrected = result.get("corrected", query)
            note = result.get("note")
            
            # Only return correction if it's different
            if corrected.lower() != query.lower():
                return corrected, note
            return query, None
            
        except Exception as e:
            logger.warning(f"AI query correction failed for '{query}': {e}. Using original.")
            return query, None
    
    @staticmethod
    def get_error_reason(tool: str, query: str, error: str) -> str:
        """
        Generate a helpful error message explaining why a query failed
        
        Args:
            tool: Tool name (weather, crypto, etc.)
            query: The query that failed
            error: Original error message
            
        Returns:
            Helpful error message with reason
        """
        if tool == "weather":
            if QueryOptimizer.is_likely_invalid(query):
                return (
                    f"No weather data found for '{query}'. "
                    f"Reason: The city name appears to be invalid or contains random characters. "
                    f"Please provide a valid city name (e.g., 'London', 'New York', 'Tokyo')."
                )
            else:
                return (
                    f"No weather data found for '{query}'. "
                    f"Reason: The city name may be misspelled or the city doesn't exist in the weather database. "
                    f"Please check the spelling and try again. Common corrections: 'Bengalore' → 'Bangalore'."
                )
        
        elif tool == "crypto":
            if QueryOptimizer.is_likely_invalid(query):
                return (
                    f"Cryptocurrency '{query}' not found. "
                    f"Reason: The coin name appears to be invalid. "
                    f"Please provide a valid cryptocurrency name (e.g., 'bitcoin', 'ethereum', 'cardano')."
                )
            else:
                return (
                    f"Cryptocurrency '{query}' not found. "
                    f"Reason: The coin name may be misspelled or not supported. "
                    f"Please check the spelling. Common examples: 'bitcoin', 'ethereum', 'btc' → 'bitcoin'."
                )
        
        elif tool == "github":
            return (
                f"Repository search for '{query}' returned no results. "
                f"Reason: The search query may be too specific or the repositories don't exist. "
                f"Try a broader search term or check the spelling."
            )
        
        else:
            return f"Error: {error}"
