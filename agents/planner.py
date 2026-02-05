"""
Planner Agent - Converts natural language tasks into structured execution plans
"""
import logging
from datetime import datetime
from typing import Dict, Any
from llm.client import get_llm_client
from models.schemas import ExecutionPlan, PlanStep

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Planner Agent uses LLM to convert user tasks into structured execution plans.
    It selects appropriate tools and defines steps.
    """
    
    AVAILABLE_TOOLS = {
        "github": {
            "name": "GitHub",
            "description": "Search repositories, get stars, contributors",
            "actions": ["search_repositories", "get_repository", "get_contributors"]
        },
        "weather": {
            "name": "Weather",
            "description": "Get current weather and forecasts",
            "actions": ["get_current_weather", "get_forecast"]
        },
        "news": {
            "name": "News",
            "description": "Get latest news articles and headlines",
            "actions": ["get_top_headlines", "search_news"]
        },
        "countries": {
            "name": "Countries",
            "description": "Get country information and data",
            "actions": ["get_country_by_name", "get_countries_by_region", "get_country_by_code"]
        },
        "crypto": {
            "name": "Crypto",
            "description": "Get cryptocurrency prices and market data",
            "actions": ["get_price", "get_trending", "get_market_data"]
        },
        "wikipedia": {
            "name": "Wikipedia",
            "description": "Search and get article summaries",
            "actions": ["search", "get_summary"]
        }
    }
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    async def create_plan(self, task: str) -> ExecutionPlan:
        """
        Create an execution plan from a natural language task
        
        Args:
            task: User's natural language task
            
        Returns:
            ExecutionPlan with structured steps
        """
        logger.info(f"Planner received task: {task}")
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)
        
        # Get structured JSON plan from LLM
        logger.info("Planner calling LLM to generate plan...")
        plan_data = await self.llm_client.generate_structured_output(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3  # Lower temperature for more consistent planning
        )
        
        logger.info(f"Planner received plan from LLM: {plan_data}")
        
        # Parse into ExecutionPlan model
        steps = []
        for step_data in plan_data["steps"]:
            logger.info(
                f"Planner parsed step {step_data.get('step_number')}: "
                f"tool={step_data.get('tool')}, action={step_data.get('action')}, "
                f"params={step_data.get('params')}"
            )
            steps.append(PlanStep(**step_data))
        
        plan = ExecutionPlan(
            task=task,
            steps=steps,
            estimated_tools=plan_data.get("estimated_tools", [])
        )
        
        logger.info(
            f"Planner created execution plan: {len(steps)} steps, "
            f"tools={plan.estimated_tools}"
        )
        
        return plan
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for the planner"""
        tools_description = "\n".join([
            f"- {tool_id}: {info['description']} | Actions: {', '.join(info['actions'])}"
            for tool_id, info in self.AVAILABLE_TOOLS.items()
        ])
        
        return f"""You are a Planner Agent in an AI Operations system. Your job is to convert natural language tasks into structured execution plans.

Available Tools:
{tools_description}

Your response MUST be valid JSON following this exact schema:
{{
  "steps": [
    {{
      "step_number": 1,
      "action": "search_repositories",
      "tool": "github",
      "params": {{"query": "machine learning", "limit": 3}},
      "reasoning": "Search for ML repositories as requested"
    }}
  ],
  "estimated_tools": ["github", "weather"]
}}

Rules:
1. Break down the task into sequential steps
2. CRITICAL: Parse the ENTIRE task - do not skip any parts. If the user asks for multiple things, create steps for ALL of them.
3. Select the most appropriate tool for each step
4. Provide clear parameters for each action - USE EXACT PARAMETER NAMES from above
5. Each step should be atomic and executable
6. Include reasoning for each step
7. Return ONLY valid JSON, no markdown or explanations
8. CRITICAL: For GitHub search_repositories, the 'query' parameter MUST NOT be empty.
   - If user asks for "top repos", use a query like "stars:>1000" or "language:python stars:>1000"
   - If user asks for repos "this month", use "pushed:>2026-01-01" or combine with other criteria
   - If user asks for repos from a specific country/company (e.g., "German tech companies"):
     * Search for the country name in repo names/descriptions: "Germany" OR "German" in:name,description
     * Or search for known companies from that country (e.g., "SAP" OR "Siemens" for Germany)
     * Combine with tech-related terms: "Germany" language:python OR "German tech" stars:>100
   - Always provide a meaningful search query, never use empty string ""
9. CRITICAL: For Wikipedia, when user asks for information/content (e.g., "brief history", "tell me about", "explain", "what is"):
   - Step 1: Use 'search' action to find the article title
   - Step 2: Use 'get_summary' action with the title from step 1 to get the actual article content
   - The 'search' action only returns titles/descriptions/URLs, NOT the article content
   - The 'get_summary' action returns the actual article extract/content
   - For informational queries, you MUST use both steps to get the content
10. CRITICAL: For News API:
   - When user asks for "latest news" or "news from [country]", prefer 'search_news' with the country name as query
   - Example: For "latest news from Germany", use search_news with query="Germany" instead of get_top_headlines with country="de"
   - The 'get_top_headlines' with only country parameter often returns 0 results
   - Use 'get_top_headlines' only when user specifically asks for "top headlines" or "headlines by category"
   - For country-specific news, use 'search_news' with query set to the country name

Example Task 1: "Find top Python repos and get weather in London"
Example Response:
{{
  "steps": [
    {{
      "step_number": 1,
      "action": "search_repositories",
      "tool": "github",
      "params": {{"query": "python", "limit": 3, "sort": "stars"}},
      "reasoning": "Search for top Python repositories"
    }},
    {{
      "step_number": 2,
      "action": "get_current_weather",
      "tool": "weather",
      "params": {{"city": "London", "units": "metric"}},
      "reasoning": "Get current weather in London"
    }}
  ],
  "estimated_tools": ["github", "weather"]
}}

Example Task 2: "Get weather in Bengalore. Give me a complete overview of Germany: its information, current weather in Berlin, latest news, and top German tech companies on GitHub"
Example Response:
{{
  "steps": [
    {{
      "step_number": 1,
      "action": "get_current_weather",
      "tool": "weather",
      "params": {{"city": "Bengalore", "units": "metric"}},
      "reasoning": "Get weather in Bengalore as requested first in the task"
    }},
    {{
      "step_number": 2,
      "action": "get_country_by_name",
      "tool": "countries",
      "params": {{"name": "Germany"}},
      "reasoning": "Get comprehensive information about Germany"
    }},
    {{
      "step_number": 3,
      "action": "get_current_weather",
      "tool": "weather",
      "params": {{"city": "Berlin", "units": "metric"}},
      "reasoning": "Get current weather in Berlin, Germany"
    }},
    {{
      "step_number": 4,
      "action": "search_news",
      "tool": "news",
      "params": {{"query": "Germany", "limit": 5}},
      "reasoning": "Get latest news about Germany"
    }},
    {{
      "step_number": 5,
      "action": "search_repositories",
      "tool": "github",
      "params": {{"query": "Germany OR German in:name,description language:python stars:>100", "limit": 5, "sort": "stars"}},
      "reasoning": "Search for top German tech companies on GitHub by searching for Germany/German in repo names and descriptions"
    }}
  ],
  "estimated_tools": ["weather", "countries", "news", "github"]
}}

Example Task 3: "Give me a brief history about Nepal"
Example Response:
{{
  "steps": [
    {{
      "step_number": 1,
      "action": "search",
      "tool": "wikipedia",
      "params": {{"query": "History of Nepal", "limit": 1}},
      "reasoning": "Search for the History of Nepal article on Wikipedia"
    }},
    {{
      "step_number": 2,
      "action": "get_summary",
      "tool": "wikipedia",
      "params": {{"title": "History of Nepal"}},
      "reasoning": "Get the actual article content/summary. The Executor will auto-extract the exact title from step 1's results if needed."
    }}
  ],
  "estimated_tools": ["wikipedia"]
}}

Note: For Wikipedia informational queries, always use search first to find the article, then get_summary to get the content. 
The Executor will automatically extract the article title from the search results if the title param matches the search query."""
    
    def _build_user_prompt(self, task: str) -> str:
        """Build user prompt with the task"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        
        return f"""Task: {task}

IMPORTANT CONTEXT:
- Current date: {current_date}
- Current month start: {current_month_start}
- When user says "this month", use: pushed:>={current_month_start}
- When user says "recent" or "latest", use dates relative to {current_date}

Create a structured execution plan for this task. Return ONLY the JSON plan."""
