import os
import json
from typing import Dict, Any

class EnterpriseMCPServer:
    """
    Simulates a secure production Model Context Protocol (MCP) Server.
    Acts as the secure data abstraction protocol fetching localized enterprise 
    compliance schemas and HR policy boundaries without exposing raw files.
    """
    def __init__(self, context_dir: str = "./enterprise_context"):
        self.context_dir = context_dir
        # Ensure our context sandbox exists safely
        os.makedirs(self.context_dir, exist_ok=True)
        self._initialize_mock_compliance_rules()

    def _initialize_mock_compliance_rules(self):
        """Creates an internal enterprise compliance policy text document."""
        policy_path = os.path.join(self.context_dir, "compliance_policy.json")
        default_policy = {
            "max_module_hours": 40,
            "required_security_inclusion": True,
            "mandatory_practical_labs": True,
            "forbidden_frameworks": ["Deprecated-Struts", "Flash-v1"]
        }
        with open(policy_path, "w") as f:
            json.dump(default_policy, f, indent=4)

    def fetch_resource(self, resource_uri: str) -> str:
        """
        MCP Standard Protocol Method to read secure internal context logs.
        E.g., resource_uri = 'mcp://compliance/corporate-rules'
        """
        if "compliance/corporate-rules" in resource_uri:
            policy_path = os.path.join(self.context_dir, "compliance_policy.json")
            with open(policy_path, "r") as f:
                data = json.load(f)
            return (
                f"ENTERPRISE COMPLIANCE RULES:\n"
                f"- Max training duration per single module: {data['max_module_hours']} hours.\n"
                f"- Every module MUST explicitly include practical hands-on labs: {data['mandatory_practical_labs']}.\n"
                f"- Architecture must completely avoid deprecated items: {', '.join(data['forbidden_frameworks'])}."
            )
        return "Error: Requested MCP Resource URI was not found or access is restricted."
