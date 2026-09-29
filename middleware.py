from typing import Any, Dict
from langchain_core.runnables import RunnableConfig, RunnableSerializable
from langchain_core.messages import BaseMessage, SystemMessage

class SafeTokenGuardMiddleware(RunnableSerializable[BaseMessage, BaseMessage]):
    """
    Custom LangChain Middleware component designed to intercept incoming requests,
    enforce system token guard-rails, and safely append standard metadata metrics.
    """
    def invoke(self, input: BaseMessage, config: RunnableConfig = None) -> BaseMessage:
        # Middleware Logic: Intercept execution context to check text safety length boundaries
        if hasattr(input, "content") and len(input.content) > 12000:
            # Safely truncate input text to avoid massive token bills or context blowouts
            input.content = input.content[:12000] + "\n...[Truncated by System Middleware Guard]..."
        
        # Merge configuration metadata tags dynamically for enhanced LangSmith indexing
        if config and "tags" not in config:
            config["tags"] = ["enterprise-ld-pipeline"]
            
        return input
