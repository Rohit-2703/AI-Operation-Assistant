"""
Pydantic models for request/response validation
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """User's task request"""
    task: str = Field(..., description="Natural language task description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": "Find the top 3 Python ML repos on GitHub and get the weather in London"
            }
        }


class TaskResponse(BaseModel):
    """Response after task submission"""
    status: str
    message: str
    run_id: Optional[str] = None
    

class PlanStep(BaseModel):
    """Individual step in the execution plan"""
    step_number: int
    action: str
    tool: str
    params: Dict[str, Any]
    reasoning: str


class ExecutionPlan(BaseModel):
    """Complete execution plan from Planner Agent"""
    task: str
    steps: List[PlanStep]
    estimated_tools: List[str]


class ToolResult(BaseModel):
    """Result from a tool execution"""
    tool: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    """Results from Executor Agent"""
    plan: ExecutionPlan
    results: List[ToolResult]
    execution_time: float


class FinalResult(BaseModel):
    """Final verified result from Verifier Agent"""
    task: str
    summary: str
    details: Dict[str, Any]
    sources: List[str]
    execution_plan: ExecutionPlan
    raw_results: List[ToolResult]
    verified: bool
    verification_notes: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    details: Optional[str] = None
    step: Optional[str] = None
