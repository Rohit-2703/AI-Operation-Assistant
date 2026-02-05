"""
Verifier Agent - Validates results and formats final output
"""
import logging
from typing import Dict, Any, List
from llm.client import get_llm_client
from models.schemas import ExecutionResult, FinalResult

logger = logging.getLogger(__name__)


class VerifierAgent:
    """
    Verifier Agent validates execution results, checks for completeness,
    and formats the final output for the user.
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    async def verify_and_format(
        self,
        task: str,
        execution_result: ExecutionResult
    ) -> FinalResult:
        """
        Verify execution results and format final output
        
        Args:
            task: Original user task
            execution_result: Results from Executor Agent
            
        Returns:
            FinalResult with verified and formatted output
        """
        logger.info(f"Verifier starting: task={task}, total_results={len(execution_result.results)}")
        
        # Check for failures
        failed_steps = [r for r in execution_result.results if not r.success]
        successful_steps = [r for r in execution_result.results if r.success]
        
        if failed_steps:
            logger.warning(
                f"Verifier detected {len(failed_steps)} failed steps: "
                f"{[f.tool for f in failed_steps]}"
            )
        
        # Extract data from successful steps
        # Handle multiple results from same tool (e.g., weather called twice for different cities)
        collected_data = {}
        sources = []
        suggestions = []
        correction_notes = []
        
        for result in successful_steps:
            if result.data:
                tool_name = result.tool
                
                # Add context to distinguish multiple calls from the same tool
                if isinstance(result.data, dict):
                    result_with_context = result.data.copy()
                    # Generic context labeling for all tools based on their return data
                    context_label = self._generate_context_label(tool_name, result_with_context)
                    if context_label:
                        result_with_context["_context"] = context_label
                else:
                    result_with_context = result.data
                
                # If same tool called multiple times, store as list
                if tool_name in collected_data:
                    # Convert existing single result to list if needed
                    if not isinstance(collected_data[tool_name], list):
                        # Add context to existing result
                        if isinstance(collected_data[tool_name], dict):
                            existing_context = self._generate_context_label(tool_name, collected_data[tool_name])
                            if existing_context:
                                collected_data[tool_name]["_context"] = existing_context
                        collected_data[tool_name] = [collected_data[tool_name]]
                    collected_data[tool_name].append(result_with_context)
                else:
                    collected_data[tool_name] = result_with_context
                
                # Extract suggestions (e.g., from news tool when no results)
                if isinstance(result.data, dict) and "suggestion" in result.data:
                    suggestions.append(result.data["suggestion"])
                
                # Extract correction notes (e.g., city name corrections)
                if isinstance(result.data, dict) and "correction_note" in result.data:
                    correction_notes.append(result.data["correction_note"])
                
                # Extract sources
                if "url" in str(result.data):
                    self._extract_sources(result.data, sources)
        
        logger.info(f"Verifier collected data from {len(collected_data)} tools: {list(collected_data.keys())}")
        
        # Use LLM to create a coherent summary
        logger.info("Verifier calling LLM to generate summary...")
        try:
            summary = await self._generate_summary(
                task=task,
                data=collected_data,
                failures=failed_steps
            )
            logger.info("Verifier successfully generated summary")
        except Exception as e:
            logger.exception(f"Verifier failed to generate summary: {str(e)}")
            summary = self._create_fallback_summary(task, collected_data, failed_steps)
        
        # Determine if results are complete
        verified = len(failed_steps) == 0
        verification_notes = None
        
        # Build comprehensive verification notes
        notes_parts = []
        
        if failed_steps:
            failed_tools = [f.tool for f in failed_steps]
            notes_parts.append(f"Some steps failed: {failed_tools}")
            # Include error messages for failed steps
            for failed in failed_steps:
                if failed.error:
                    notes_parts.append(f"- {failed.tool}: {failed.error}")
        
        if suggestions:
            notes_parts.append("Suggestions:")
            for suggestion in suggestions:
                notes_parts.append(f"- {suggestion}")
        
        if correction_notes:
            notes_parts.append("Corrections applied:")
            for correction in correction_notes:
                notes_parts.append(f"- {correction}")
        
        verification_notes = "\n".join(notes_parts) if notes_parts else None
        
        logger.info(f"Verifier completed: verified={verified}, summary_length={len(summary)}")
        
        return FinalResult(
            task=task,
            summary=summary,
            details=collected_data,
            sources=sources,
            execution_plan=execution_result.plan,
            raw_results=execution_result.results,
            verified=verified,
            verification_notes=verification_notes
        )
    
    async def _generate_summary(
        self,
        task: str,
        data: Dict[str, Any],
        failures: List
    ) -> str:
        """
        Use LLM to generate a coherent summary of results
        
        Args:
            task: Original task
            data: Collected data from tools
            failures: List of failed steps
            
        Returns:
            Summary string
        """
        system_prompt = """You are a Verifier Agent that creates clear, concise summaries of task execution results.

Your job:
1. Synthesize information from multiple tool outputs
2. Present results in a user-friendly format using Markdown
3. Highlight key findings with bold text (**text**)
4. Use bullet points (-) or numbered lists for multiple items
5. Use headers (##) for major sections if needed
6. Note any failures or missing data
7. Format numbers, dates, and metrics clearly
8. When multiple results exist for the same tool, list each one clearly

IMPORTANT: Return your summary in Markdown format. Use Markdown syntax for formatting:
- **bold** for emphasis
- *italic* for subtle emphasis
- ## Headers for sections
- - Bullet points for lists
- `code` for technical terms
- [links](url) for URLs

Keep summaries concise but informative and well-formatted. Use bullet points and headers to organize information clearly."""
        
        user_prompt = f"""Original Task: {task}

Collected Data:
{self._format_data_for_summary(data)}
{f"Failed steps: {[f.tool for f in failures]}" if failures else ""}

Create a clear, well-organized summary using Markdown formatting. Use bullet points, headers, and bold text to structure the information. Include all relevant details from the data. Make sure to mention ALL results, including when the same tool was called multiple times."""
        
        try:
            summary = await self.llm_client.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=2000  # Increased from 500 to prevent truncation
            )
            return summary.strip()
        except Exception as e:
            # Fallback to simple summary if LLM fails
            return self._create_fallback_summary(task, data, failures)
    
    def _format_data_for_summary(self, data: Dict[str, Any]) -> str:
        """Format collected data for LLM summary"""
        lines = []
        for tool, tool_data in data.items():
            lines.append(f"\n{tool.upper()}:")
            # Handle multiple results from same tool (stored as list)
            if isinstance(tool_data, list):
                for idx, item in enumerate(tool_data, 1):
                    lines.append(f"  Result {idx}:")
                    lines.append(self._stringify_data(item, indent=3))
            else:
                lines.append(self._stringify_data(tool_data, indent=2))
        return "\n".join(lines)
    
    def _stringify_data(self, data: Any, indent: int = 0) -> str:
        """Convert data to readable string format"""
        prefix = "  " * indent
        
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._stringify_data(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data[:3], 1):  # Limit to first 3 items
                lines.append(f"{prefix}[{i}]:")
                lines.append(self._stringify_data(item, indent + 1))
            if len(data) > 3:
                lines.append(f"{prefix}... and {len(data) - 3} more")
            return "\n".join(lines)
        else:
            return f"{prefix}{data}"
    
    def _create_fallback_summary(
        self,
        task: str,
        data: Dict[str, Any],
        failures: List
    ) -> str:
        """Create a simple summary if LLM fails"""
        success_count = len(data)
        failure_count = len(failures)
        
        summary = f"Task: {task}\n\n"
        summary += f"Executed {success_count + failure_count} steps. "
        summary += f"{success_count} successful, {failure_count} failed.\n\n"
        
        if data:
            summary += "Results:\n"
            for tool in data.keys():
                summary += f"- {tool.capitalize()} data retrieved\n"
        
        return summary
    
    def _generate_context_label(self, tool_name: str, data: Dict[str, Any]) -> str:
        """
        Generate a context label to distinguish multiple calls from the same tool.
        This helps the LLM understand what each result represents.
        
        Args:
            tool_name: Name of the tool
            data: Result data from the tool
            
        Returns:
            Context label string or None
        """
        if tool_name == "weather" and "city" in data:
            return f"Weather for {data['city']}"
        elif tool_name == "github" and "query" in data:
            # Truncate long queries for readability
            query = data["query"]
            if len(query) > 50:
                query = query[:47] + "..."
            return f"GitHub search: {query}"
        elif tool_name == "news" and "query" in data:
            return f"News about {data['query']}"
        elif tool_name == "wikipedia":
            if "title" in data:
                return f"Wikipedia: {data['title']}"
            elif "query" in data:
                return f"Wikipedia search: {data['query']}"
        elif tool_name == "crypto" and "coin" in data:
            return f"Crypto: {data['coin']}"
        elif tool_name == "countries":
            if "name" in data:
                return f"Country: {data['name']}"
            elif "region" in data:
                return f"Region: {data['region']}"
        
        return None
    
    def _extract_sources(self, data: Any, sources: List[str]):
        """Recursively extract URLs from data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ["url", "html_url"] and isinstance(value, str):
                    if value not in sources:
                        sources.append(value)
                elif isinstance(value, (dict, list)):
                    self._extract_sources(value, sources)
        elif isinstance(data, list):
            for item in data:
                self._extract_sources(item, sources)
