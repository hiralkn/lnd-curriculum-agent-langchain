import streamlit as st
import asyncio
import json
from agent import app

st.set_page_config(
    page_title="L&D Curriculum State Machine", 
    page_icon="🤖", 
    layout="wide"
)

st.title("🤖 Automated Corporate L&D Curriculum Agent")
st.caption("CV Architecture Demo: Managed LangGraph State Machine with Playwright Web-Scraping & MCP Compliance Filters")

# Sidebar Configuration for tracking observability metadata
st.sidebar.header("⚙️ Agent Workspace Settings")
thread_id = st.sidebar.text_input("LangGraph Session Thread ID", "streamlit-session-404")
st.sidebar.info(
    "This thread ID maintains the short-term checkpointer state memory in LangGraph, "
    "allowing multi-turn critiques between the Designer and Reviewer nodes."
)

# User inputs
target_role = st.text_input(
    "🎯 Targeted Upskilling Role / Skill Gap Goal:", 
    "Junior Backend Developer to Production AWS Cloud Engineer"
)
competitor_url = st.text_input(
    "🌐 Competitor/Industry Syllabus URL for Live Benchmarking:", 
    "https://amazon.com"
)

if st.button("Execute Multi-Agent Refinement Loop", type="primary"):
    with st.spinner("Executing State Graph nodes... Scraping targets, verifying via MCP, and finalizing schema."):
        
        # Configure state configuration variables
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "target_role": target_role,
            "competitor_url": competitor_url,
            "iterations": 0
        }
        
        try:
            # Execute the workflow inside Streamlit's runtime engine environment
            final_state = asyncio.run(app.ainvoke(initial_state, config))
            output_data = final_state.get("final_output")
            
            if output_data:
                st.success("🎉 Curriculum Blueprint Generated & Verified by QA Reviewer Node!")
                
                # Display structural properties
                st.subheader(f"📋 Course Title: {output_data.get('curriculum_title')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Target Designation Role", value=output_data.get('target_role'))
                with col2:
                    st.metric(label="Total Program Duration", value=f"{output_data.get('total_duration_weeks')} Weeks")
                
                # Display individual modules
                st.markdown("### 📚 Sequential Training Modules")
                for index, mod in enumerate(output_data.get("modules", [])):
                    with st.expander(f"🔹 Module {index + 1}: {mod.get('module_name')} ({mod.get('estimated_hours')} Hours)"):
                        st.write("**Core Frameworks & Concepts Covered:**")
                        for topic in mod.get("topics_covered", []):
                            st.write(f"- {topic}")
                        st.write("**Mandatory Hands-on Engineering Labs:**")
                        for lab in mod.get("practical_labs", []):
                            st.write(f"- 🧪 {lab}")
                
                # Display Capstone Details
                st.markdown("### 🏆 Production Capstone Project Blueprint")
                st.info(output_data.get("capstone_project_details"))
                
                # Provide direct JSON download button
                json_string = json.dumps(output_data, indent=2)
                st.download_button(
                    label="💾 Export Production JSON Schema",
                    data=json_string,
                    file_name="curriculum_schema.json",
                    mime="application/json"
                )
            else:
                st.error("Pipeline finished execution but failed to output a verified structured draft schema.")
                
        except Exception as e:
            st.error(f"Execution Engine Error: {e}")
