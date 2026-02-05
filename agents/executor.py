"""
Executor Agent - Executes plans by calling appropriate tools/APIs
"""
import logging
import time
import asyncio
from typing import List

from models.schemas import ExecutionPlan, ToolResult, ExecutionResult
from tools import (
    GitHubTool,
    WeatherTool,
    NewsTool,
    CountriesTool,
    CryptoTool,
    WikipediaTool,
)

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    Executor Agent executes the plan created by Planner Agent.
    It calls the appropriate tools and collects results.
    """
    
    def __init__(self):
        # Initialize all tools
        self.tools = {
            "github": GitHubTool(),
            "weather": WeatherTool(),
            "news": NewsTool(),
            "countries": CountriesTool(),
            "crypto": CryptoTool(),
            "wikipedia": WikipediaTool()
        }
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Execute the plan step by step
        
        Args:
            plan: ExecutionPlan from Planner Agent
            
        Returns:
            ExecutionResult with results from each step
        """
        logger.info(
            "Executor starting plan",
            extra={
                "task": plan.task,
                "total_steps": len(plan.steps),
            },
        )

        start_time = time.time()
        results: List[ToolResult] = []
        
        # Process steps with smart parallelization:
        # - Independent steps run in parallel
        # - Steps that depend on previous results run sequentially
        i = 0
        while i < len(plan.steps):
            # Collect a batch of independent steps that can run in parallel
            parallel_batch = []
            batch_start = i
            
            while i < len(plan.steps):
                step = plan.steps[i]
                
                # Check if this step depends on previous results
                depends_on_previous = (
                    step.tool == "wikipedia" and step.action == "get_summary" and
                    i > 0 and plan.steps[i-1].tool == "wikipedia" and
                    plan.steps[i-1].action == "search"
                )
                
                if depends_on_previous and len(parallel_batch) > 0:
                    # Execute accumulated parallel batch first, then handle this dependent step
                    break
                
                parallel_batch.append((i, step))
                i += 1
            
            # Execute parallel batch if we have one
            if parallel_batch:
                if len(parallel_batch) > 1:
                    logger.info(f"Executor running {len(parallel_batch)} steps in parallel: steps {[s.step_number for _, s in parallel_batch]}")
                else:
                    logger.info(f"Executor running step {parallel_batch[0][1].step_number}")
                
                async def execute_with_index(idx_and_step):
                    idx, step = idx_and_step
                    step_start_time = time.time()
                    logger.info(
                        f"Executor STARTING step {step.step_number} (tool={step.tool}, action={step.action}) at {step_start_time:.3f}",
                        extra={
                            "step_number": step.step_number,
                            "action": step.action,
                            "tool": step.tool,
                            "params": step.params,
                        },
                    )
                    result = await self._execute_step(step)
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    logger.info(
                        f"Executor COMPLETED step {step.step_number} (tool={step.tool}) in {step_duration:.3f}s at {step_end_time:.3f}",
                        extra={
                            "step_number": step.step_number,
                            "tool": result.tool,
                            "success": result.success,
                            "error": result.error,
                            "duration": step_duration,
                        },
                    )
                    return (idx, result)
                
                # Run all steps in batch concurrently using asyncio.gather
                batch_start_time = time.time()
                logger.info(f"Executor starting parallel batch execution at {batch_start_time:.3f}")
                batch_results = await asyncio.gather(*[execute_with_index(task) for task in parallel_batch])
                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                logger.info(f"Executor completed parallel batch in {batch_duration:.3f}s (all {len(parallel_batch)} steps ran concurrently)")
                
                # Sort by original index to maintain step order
                batch_results.sort(key=lambda x: x[0])
                results.extend([r for _, r in batch_results])
            
            # Handle dependent step if we broke out of the loop
            if i < len(plan.steps):
                step = plan.steps[i]
                logger.info(
                    "Executor running dependent step",
                    extra={
                        "step_number": step.step_number,
                        "action": step.action,
                        "tool": step.tool,
                        "params": step.params,
                    },
                )
                
                # Smart parameter injection: If this is wikipedia.get_summary and previous step was wikipedia.search,
                # automatically extract the title from the search results
                if (step.tool == "wikipedia" and step.action == "get_summary" and 
                    len(results) > 0 and results[-1].tool == "wikipedia" and 
                    results[-1].success and results[-1].data):
                    prev_result = results[-1].data
                    # If title param is missing or matches the search query, use first result from search
                    if "title" not in step.params or step.params.get("title") == prev_result.get("query"):
                        if prev_result.get("results") and len(prev_result["results"]) > 0:
                            extracted_title = prev_result["results"][0]["title"]
                            step.params["title"] = extracted_title
                            logger.info(
                                f"Executor auto-extracted title from previous search: {extracted_title}"
                            )
                
                result = await self._execute_step(step)
                logger.info(
                    "Executor finished dependent step",
                    extra={
                        "step_number": step.step_number,
                        "tool": result.tool,
                        "success": result.success,
                        "error": result.error,
                    },
                )
                results.append(result)
                i += 1
        
        execution_time = time.time() - start_time
        logger.info(
            "Executor completed plan",
            extra={
                "task": plan.task,
                "execution_time": execution_time,
            },
        )
        
        return ExecutionResult(
            plan=plan,
            results=results,
            execution_time=execution_time
        )
    
    async def _execute_step(self, step) -> ToolResult:
        """
        Execute a single step
        
        Args:
            step: PlanStep to execute
            
        Returns:
            ToolResult with success/failure and data
        """
        tool_name = step.tool
        action = step.action
        params = step.params
        
        logger.info(
            f"Executor executing step: tool={tool_name}, action={action}, "
            f"params={params}"
        )
        
        try:
            # Get the tool instance
            tool = self.tools.get(tool_name)
            if not tool:
                logger.error(f"Tool '{tool_name}' not found")
                return ToolResult(
                    tool=tool_name,
                    success=False,
                    error=f"Tool '{tool_name}' not found"
                )
            
            # Get the action method
            if not hasattr(tool, action):
                logger.error(f"Action '{action}' not found in tool '{tool_name}'")
                return ToolResult(
                    tool=tool_name,
                    success=False,
                    error=f"Action '{action}' not found in tool '{tool_name}'"
                )
            
            method = getattr(tool, action)
            
            # Filter params to only include what the method accepts
            import inspect
            sig = inspect.signature(method)
            valid_params = set(sig.parameters.keys())
            filtered_params = {k: v for k, v in params.items() if k in valid_params}
            
            if filtered_params != params:
                removed = set(params.keys()) - set(filtered_params.keys())
                logger.warning(
                    f"Executor filtering out unsupported params for {tool_name}.{action}: "
                    f"{removed}. Using: {filtered_params}"
                )
            
            # Execute the action with filtered parameters
            logger.info(f"Executor calling {tool_name}.{action} with params: {filtered_params}")
            result_data = await method(**filtered_params)
            
            # Check if the tool itself returned success flag
            if isinstance(result_data, dict) and "success" in result_data:
                success = result_data["success"]
                if success:
                    logger.info(
                        f"Executor step completed successfully: tool={tool_name}, "
                        f"action={action}"
                    )
                    return ToolResult(
                        tool=tool_name,
                        success=True,
                        data=result_data
                    )
                else:
                    error_msg = result_data.get("error", "Unknown error")
                    logger.warning(
                        f"Executor step failed: tool={tool_name}, action={action}, "
                        f"error={error_msg}"
                    )
                    return ToolResult(
                        tool=tool_name,
                        success=False,
                        error=error_msg
                    )
            
            # If no success flag, assume success
            logger.info(
                f"Executor step completed (no success flag): tool={tool_name}, "
                f"action={action}"
            )
            return ToolResult(
                tool=tool_name,
                success=True,
                data=result_data
            )
            
        except Exception as e:
            logger.exception(
                f"Executor step raised exception: tool={tool_name}, "
                f"action={action}, error={str(e)}"
            )
            return ToolResult(
                tool=tool_name,
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    async def close(self):
        """Close all tool HTTP clients"""
        for tool in self.tools.values():
            if hasattr(tool, "close"):
                await tool.close()
