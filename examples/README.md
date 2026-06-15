# ActionRail Finance — Agent Integration Examples

This directory contains clean, dependency-free examples demonstrating how to integrate AI agents and automated workflows with **ActionRail Finance**.

## Examples Included

1. **[`agent_client.py`](agent_client.py)**:
   * A lightweight client using the standard library `urllib.request`.
   * Shows how to handle authentication headers, generate idempotency keys, submit preflight checks, and implement decision handling rules (`allow`, `approval_required`, `blocked`, `needs_more_evidence`).
2. **[`langgraph_actionrail_tool.py`](langgraph_actionrail_tool.py)**:
   * Demonstrates how to wrap ActionRail's preflight API as a tool for agentic workflows (like LangGraph or LangChain).
   * Includes pseudo-code showing how to design routing edges based on ActionRail's deterministic decisions.
3. **[`openapi_tool_schema.json`](openapi_tool_schema.json)**:
   * A standard OpenAPI / OpenAI function calling schema for the `request_finance_action_preflight` tool.
   * Helps LLMs accurately understand when and how to invoke ActionRail preflight before attempting any financial mutations.

---

## Quickstart

### 1. Ensure ActionRail is running locally

In your main terminal, start the ActionRail server:

```bash
uvicorn app.main:app --reload
```

### 2. Run the agent client example

Run the demo script:

```bash
python examples/agent_client.py
```

### Notes

* **API Key Security**: If ActionRail is configured in secure mode (`ACTIONRAIL_REQUIRE_API_KEY=1`), make sure to create an API key via the Admin dashboard (`http://127.0.0.1:8000/dashboard/admin/api-clients`) and update the placeholder `<local-demo-agent-key>` inside `examples/agent_client.py`.
* **Safety Boundary**: All actions triggered by the examples execute within the local SQLite instance. **No real money movement or ERP mutation occurs.**
