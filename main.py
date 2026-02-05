"""
Main FastAPI application for AI Operations Assistant
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import TaskRequest, ErrorResponse
from workflows.ai_ops_workflow import (
    planner_step,
    executor_step,
    verifier_step,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sanitize httpx logs to prevent API key exposure
# Set httpx logger to WARNING level to avoid logging request URLs with API keys
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(" AI Operations Assistant starting up...")

    required_vars = ["OPENAI_API_KEY", "OPENWEATHERMAP_API_KEY", "NEWS_API_KEY"]
    missing_vars = [v for v in required_vars if not os.getenv(v)]

    if missing_vars:
        logger.warning(f" Missing env vars: {missing_vars}")
    else:
        logger.info(" All required environment variables are set")

    yield

    logger.info(" Shutting down AI Operations Assistant...")


# Create FastAPI app
app = FastAPI(
    title="AI Operations Assistant",
    description="Multi-agent AI system for real-world operations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AI Operations Assistant API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post(
    "/api/task/execute",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def execute_task(request: TaskRequest):
    """
    Execute the full AI Ops pipeline (Planner → Executor → Verifier).
    Returns results immediately for the Streamlit UI.
    """
    try:
        task = request.task.strip()
        if not task:
            raise HTTPException(status_code=400, detail="Task cannot be empty")

        logger.info(f" Execute task: {task}")

        # Execute the multi-agent pipeline
        plan = await planner_step(task)
        execution_result = await executor_step(plan)
        final_result = await verifier_step(task, execution_result)

        return final_result

    except HTTPException:
        # Re-raise FastAPI HTTP errors as-is
        raise
    except Exception as e:
        logger.exception(" Failed to execute task directly")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def list_tools():
    from agents.planner import PlannerAgent

    return {
        "total_tools": len(PlannerAgent.AVAILABLE_TOOLS),
        "tools": PlannerAgent.AVAILABLE_TOOLS,
    }


@app.get("/api/examples")
async def get_examples():
    return {
        "examples": [
            "Get weather in London.",
            "Find top Python GitHub repositories from this month",
            "What is the weather in Bangalore right now and give me the current news about this city?",
            
        ]
    }
