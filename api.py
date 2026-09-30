import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

# Import your compiled LangGraph application from agent.py
from agent import app

# Initialize FastAPI App
server = FastAPI(
    title="L&D Curriculum Deep Agent API",
    description="Production API hosting a multi-agent LangGraph workflow with cognitive reflection loops.",
    version="1.0.0"
)

# Enable CORS so you can connect frontends or internal tools easily
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

# Define the structured HTTP Request payload schema using Pydantic
class CurriculumGenerationRequest(BaseModel):
    target_role: str = Field(..., description="The exact job profile or corporate role targeting the curriculum.")
    competitor_url: Optional[str] = Field(None, description="Optional live competitor syllabus URL to extract benchmarks from.")

# Define the structured HTTP Response layout
class CurriculumGenerationResponse(BaseModel):
    session_id: str
    iterations_run: int
    curriculum: Dict[str, Any]

@server.get("/health")
def health_check():
    """Simple status endpoint for Render to monitor application stability."""
    return {"status": "healthy", "service": "ld-deep-agent"}

@server.post("/api/v1/generate", response_model=CurriculumGenerationResponse)
async def generate_curriculum(payload: CurriculumGenerationRequest):
    """Invokes the LangGraph pipeline asynchronously to generate structured courses."""
    try:
        # 1. Establish initial data tracking properties for our shared AgentState
        initial_state = {
            "target_role": payload.target_role,
            "competitor_url": payload.competitor_url if payload.competitor_url else "None",
            "scraped_raw_data": "",
            "current_draft": {},
            "review_feedback": "",
            "iterations": 0,
            "final_output": {},
            "active_plan": [],
            "critique_log": []
        }
        
        # 2. Generate a unique thread ID to isolate this memory session cleanly
        session_thread_id = str(uuid.uuid4())
        execution_config = {"configurable": {"thread_id": session_thread_id}}
        
        print(f"🚀 [API] Triggering Deep Agent graph run. Thread ID: {session_thread_id}")
        
        # 3. Stream data asynchronously from your compiled app node steps
        final_state = await app.ainvoke(initial_state, config=execution_config)
        
        # 4. Extract data cleanly or handle an edge-case empty generation failure
        final_output_data = final_state.get("final_output")
        if not final_output_data:
            # Fallback to current draft if max iterations reached without clean approval
            final_output_data = final_state.get("current_draft", {})
            
        if not final_output_data:
            raise HTTPException(status_code=500, detail="The agent network failed to construct a valid curriculum.")

        return CurriculumGenerationResponse(
            session_id=session_thread_id,
            iterations_run=final_state.get("iterations", 0),
            curriculum=final_output_data
        )
        
    except Exception as e:
        print(f"❌ [API Error] Generation thread failure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal agent execution error: {str(e)}")
