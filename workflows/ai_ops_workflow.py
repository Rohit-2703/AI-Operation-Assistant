"""
AI Operations Workflow - Step functions for the multi-agent pipeline
"""

import logging
from agents import PlannerAgent, ExecutorAgent, VerifierAgent

logger = logging.getLogger(__name__)


async def planner_step(task: str):
    logger.info(f"Planner step starting for task: {task}")
    
    planner = PlannerAgent()
    plan = await planner.create_plan(task)
    
    plan_dict = {
        "task": plan.task,
        "steps": [
            {
                "step_number": s.step_number,
                "action": s.action,
                "tool": s.tool,
                "params": s.params,
                "reasoning": s.reasoning,
            }
            for s in plan.steps
        ],
        "estimated_tools": plan.estimated_tools,
    }
    
    logger.info(
        f"Planner step completed: generated {len(plan.steps)} steps, "
        f"tools={plan.estimated_tools}"
    )
    
    return plan_dict


async def executor_step(plan: dict):

    from models.schemas import ExecutionPlan, PlanStep

    steps = [PlanStep(**s) for s in plan["steps"]]

    execution_plan = ExecutionPlan(
        task=plan["task"],
        steps=steps,
        estimated_tools=plan["estimated_tools"],
    )

    executor = ExecutorAgent()
    result = await executor.execute_plan(execution_plan)
    await executor.close()

    return {
        "plan": plan,
        "results": [
            {
                "tool": r.tool,
                "success": r.success,
                "data": r.data,
                "error": r.error,
            }
            for r in result.results
        ],
        "execution_time": result.execution_time,
    }


async def verifier_step(task: str, execution_result: dict):
    logger.info(f"Verifier step starting for task: {task}")
    
    from models.schemas import (
        ExecutionResult,
        ExecutionPlan,
        PlanStep,
        ToolResult,
    )

    plan_data = execution_result["plan"]

    steps = [PlanStep(**s) for s in plan_data["steps"]]

    plan = ExecutionPlan(
        task=plan_data["task"],
        steps=steps,
        estimated_tools=plan_data["estimated_tools"],
    )

    results = [ToolResult(**r) for r in execution_result["results"]]

    exec_result = ExecutionResult(
        plan=plan,
        results=results,
        execution_time=execution_result["execution_time"],
    )

    verifier = VerifierAgent()
    final = await verifier.verify_and_format(task, exec_result)
    
    logger.info(f"Verifier step completed: verified={final.verified}")

    return {
        "task": final.task,
        "summary": final.summary,
        "details": final.details,
        "sources": final.sources,
        "execution_plan": plan_data,
        "verified": final.verified,
        "verification_notes": final.verification_notes,
    }


