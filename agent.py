import os
from typing import List, Dict, Any, TypedDict, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Import our custom components from prior phases
from tools import scrape_competitor_syllabus
from schema import CorporateSyllabus
from middleware import SafeTokenGuardMiddleware

load_dotenv()

# ==========================================
# 1. DEFINE LANGGRAPH STATE (Deep Agent Channels Added)
# ==========================================
class AgentState(TypedDict):
    target_role: str
    competitor_url: str
    scraped_raw_data: str
    current_draft: Dict[str, Any]
    review_feedback: str
    iterations: int
    final_output: Dict[str, Any]
    # --- Deep Agent Cognitive Slots ---
    active_plan: List[str]          # Dynamic sub-tasks currently being computed
    critique_log: List[str]         # Tracks internal reasoning history over iterations

# ==========================================
# 2. INITIALIZE CORE LLM & MIDDLEWARE
# ==========================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
middleware_guard = SafeTokenGuardMiddleware()

# Bind the structured output schema strictly to the model
structured_llm = llm.with_structured_output(CorporateSyllabus)

# ==========================================
# 3. DEFINE THE AGENT NODES
# ==========================================

async def research_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Uses Playwright to extract live industry benchmarks."""
    print("🤖 [Research Node] Scraping live benchmarks via Playwright...")
    url = state.get("competitor_url")
    
    if url and url.startswith("http"):
        scraped_text = await scrape_competitor_syllabus.ainvoke(url)
    else:
        scraped_text = "No valid live URL provided. Proceeding with standard industry knowledge."
        
    return {"scraped_raw_data": scraped_text, "iterations": 0}


def planner_node(state: AgentState) -> Dict[str, Any]:
    """NEW Node: Deep Agent Cognitive Component. Dynamic strategy adjustments."""
    print(f"🧠 [Planner Node] Reviewing critiques. Generating optimization roadmap...")
    
    feedback = state.get("review_feedback", "Initial Plan Execution.")
    target_role = state.get("target_role")
    
    planner_prompt = (
        "You are an Elite L&D Strategy Director. Your goal is to look at the targets and critiques, "
        "and break down a step-by-step strategy for the Designer to follow.\n\n"
        f"Target Role: {target_role}\n"
        f"Latest Feedback: {feedback}\n\n"
        "Output exactly 3 clear instructions (one per line) focusing on fixing the critiques or maximizing the role depth. "
        "Do not output conversational filler, introductory text, or markdown symbols."
    )
    
    response = llm.invoke([SystemMessage(content=planner_prompt)])
    instructions = [line.strip() for line in response.content.split("\n") if line.strip()]
    
    # Initialize or append to tracking logs
    current_log = state.get("critique_log", [])
    if current_log is None:
        current_log = []
        
    return {
        "active_plan": instructions,
        "critique_log": current_log + [f"Iteration {state.get('iterations', 0)}: {feedback}"]
    }


def designer_node(state: AgentState) -> Dict[str, Any]:
    """Node 2 (Updated): Drafts the curriculum factoring in the Planner's instructions."""
    print(f"🎨 [Designer Node] Drafting curriculum. Iteration: {state['iterations'] + 1}")
    
    # Read the dynamic plan injected by the Deep Planner
    current_plan = "\n".join([f"- {task}" for task in state.get("active_plan", [])])
    
    system_prompt = (
        "You are an expert Corporate L&D Instructional Designer. Your job is to create "
        "a cutting-edge curriculum targeting the user's requested role.\n\n"
        f"Target Role: {state['target_role']}\n"
        f"Live Industry Data: {state['scraped_raw_data']}\n"
        f"Strategic Plan To Follow:\n{current_plan}\n\n"  # Deep Architecture Layer
        f"Prior Review Feedback (if any): {state.get('review_feedback', 'None. This is your first draft.')}"
    )
    
    # Bundle input and route it through our custom LangChain middleware
    raw_message = HumanMessage(content="Generate a complete curriculum matching these constraints.")
    processed_message = middleware_guard.invoke(raw_message)
    
    # Invoke the model with structured constraints enforced
    response = structured_llm.invoke([SystemMessage(content=system_prompt), processed_message])
    
    # Store the output structured dictionary into the state context
    return {
        "current_draft": response.model_dump(), 
        "iterations": state["iterations"] + 1
    }


from mcp_server import EnterpriseMCPServer

# Instantiate our MCP Connection
mcp_client = EnterpriseMCPServer()

def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Evaluates the draft for safety, depth, and MCP enterprise compliance."""
    print("🧐 [Reviewer Node] Auditing current curriculum draft via MCP rules...")
    draft = state["current_draft"]
    
    # Securely pull compliance constraints through the MCP protocol layer
    mcp_compliance_context = mcp_client.fetch_resource("mcp://compliance/corporate-rules")
    
    # Inject both the draft and the secure MCP rules into the prompt
    eval_prompt = (
        "You are a strict Corporate L&D Director. Review this curriculum draft for quality.\n\n"
        f"{mcp_compliance_context}\n\n"
        "Verify if the draft complies with all corporate rules listed above. If it is high quality "
        "and adheres fully to the guidelines, respond with exactly 'APPROVED'. "
        "If it breaks any rule or needs updates, provide explicit bulleted feedback on what to change.\n\n"
        f"Draft to Review:\n{draft}"
    )
    
    response = llm.invoke([SystemMessage(content=eval_prompt)])
    feedback = response.content.strip()
    
    if "APPROVED" in feedback:
        return {"review_feedback": "APPROVED", "final_output": draft}
    else:
        return {"review_feedback": feedback}


# ==========================================
# 4. DEFINE CONDITIONAL ROUTING LOGIC (Updated to point to Planner)
# ==========================================
def route_approval(state: AgentState) -> Literal["planner", "__end__"]:
    """Determines whether to loop back to the Planner for optimization or conclude the graph workflow."""
    if state.get("review_feedback") == "APPROVED":
        print("✅ [Workflow] Deep Agent Optimization Validated and Approved!")
        return END
    
    if state["iterations"] >= 3:
        print("⚠️ [Workflow] Maximum iterations reached. Forcing fallback approval.")
        return END
        
    print(f"🔄 [Workflow] Draft rejected. Routing to Planner for strategy recalculation. Feedback: {state['review_feedback']}")
    return "planner"  # Routes back to the planner instead of straight to the designer

# ==========================================
# 5. ASSEMBLE THE WORKFLOW GRAPH
# ==========================================
workflow = StateGraph(AgentState)

# Add our independent processing modules (Added planner node here)
workflow.add_node("research", research_node)
workflow.add_node("planner", planner_node)
workflow.add_node("designer", designer_node)
workflow.add_node("reviewer", reviewer_node)

# Map edge connections chronologically
workflow.add_edge(START, "research")
workflow.add_edge("research", "planner")        # Routes from Research straight into Strategy Planning
workflow.add_edge("planner", "designer")
workflow.add_edge("designer", "reviewer")

# Attach the iterative critique fallback loop
workflow.add_conditional_edges("reviewer", route_approval)

# Integrate Short-Term Memory Checkpointing
memory_engine = MemorySaver()
app = workflow.compile(checkpointer=memory_engine)
