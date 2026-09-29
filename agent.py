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
# 1. DEFINE LANGGRAPH STATE
# ==========================================
class AgentState(TypedDict):
    target_role: str
    competitor_url: str
    scraped_raw_data: str
    current_draft: Dict[str, Any]
    review_feedback: str
    iterations: int
    final_output: Dict[str, Any]

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


def designer_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Drafts the curriculum based on research and prior critique."""
    print(f"🎨 [Designer Node] Drafting curriculum. Iteration: {state['iterations'] + 1}")
    
    system_prompt = (
        "You are an expert Corporate L&D Instructional Designer. Your job is to create "
        "a cutting-edge curriculum targeting the user's requested role.\n\n"
        f"Target Role: {state['target_role']}\n"
        f"Live Industry Data: {state['scraped_raw_data']}\n"
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
# 4. DEFINE CONDITIONAL ROUTING LOGIC
# ==========================================
def route_approval(state: AgentState) -> Literal["designer", "__end__"]:
    """Determines whether to loop back and fix the design or conclude the graph workflow."""
    if state.get("review_feedback") == "APPROVED":
        print("✅ [Workflow] Curriculum Approved by QA Node!")
        return END
    
    if state["iterations"] >= 3:
        print("⚠️ [Workflow] Maximum iterations reached. Forcing fallback approval.")
        return END
        
    print(f"🔄 [Workflow] Draft rejected. Routing back to Designer. Feedback: {state['review_feedback']}")
    return "designer"

# ==========================================
# 5. ASSEMBLE THE WORKFLOW GRAPH
# ==========================================
workflow = StateGraph(AgentState)

# Add our independent processing modules
workflow.add_node("research", research_node)
workflow.add_node("designer", designer_node)
workflow.add_node("reviewer", reviewer_node)

# Map edge connections chronologically
workflow.add_edge(START, "research")
workflow.add_edge("research", "designer")
workflow.add_edge("designer", "reviewer")

# Attach the iterative critique fallback loop
workflow.add_conditional_edges("reviewer", route_approval)

# Integrate Short-Term Memory Checkpointing
memory_engine = MemorySaver()
app = workflow.compile(checkpointer=memory_engine)
