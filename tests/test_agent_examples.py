import json
import os
from pathlib import Path

def test_agent_client_importable():
    """Verify that agent_client can be imported without network calls and has the client class."""
    from examples.agent_client import ActionRailClient
    assert ActionRailClient is not None
    
    # Test client initialization works
    client = ActionRailClient(base_url="http://127.0.0.1:8000", api_key="sk_test")
    assert client.base_url == "http://127.0.0.1:8000"
    assert client.api_key == "sk_test"


def test_langgraph_tool_importable():
    """Verify that langgraph_actionrail_tool can be imported and contains the preflight tool function."""
    from examples.langgraph_actionrail_tool import request_finance_action_preflight
    assert request_finance_action_preflight is not None


def test_openapi_tool_schema_valid():
    """Verify that openapi_tool_schema.json exists, is valid JSON, and has the correct tool name."""
    repo_root = Path(__file__).resolve().parent.parent
    schema_path = repo_root / "examples" / "openapi_tool_schema.json"
    
    assert schema_path.exists()
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    assert isinstance(schema, dict)
    assert schema.get("type") == "function"
    assert schema.get("function", {}).get("name") == "request_finance_action_preflight"
    assert "required" in schema["function"]["parameters"]


def test_docs_and_examples_links_exist():
    """Verify all files mentioned in the agent documentation exist on disk."""
    repo_root = Path(__file__).resolve().parent.parent
    
    expected_files = [
        "docs/AGENT_INTEGRATION.md",
        "examples/README.md",
        "examples/agent_client.py",
        "examples/langgraph_actionrail_tool.py",
        "examples/openapi_tool_schema.json",
    ]
    
    for relative_path in expected_files:
        full_path = repo_root / relative_path
        assert full_path.exists(), f"File {relative_path} not found"
