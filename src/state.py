# src/state.py
from typing import Annotated, Sequence, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Inputs & Core Outputs
    target_role: str
    competitor_url: str
    scraped_raw_data: str
    current_draft: Dict[str, Any]
    final_output: Dict[str, Any]
    
    # Deep Agent Cognitive State Channels
    active_plan: List[str]          # Dynamic sub-tasks currently being computed
    critique_log: List[str]         # Track internal reasoning history
    review_feedback: str
    iterations: int
