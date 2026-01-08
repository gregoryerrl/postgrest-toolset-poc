"""
ADK Agent using MCP Toolbox for Databases.

This POC demonstrates Google's official solution for connecting
ADK agents to PostgreSQL databases.
"""

import os
import asyncio
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from toolbox_core import ToolboxSyncClient

load_dotenv()

# Configuration
TOOLBOX_URL = os.getenv("TOOLBOX_URL", "http://127.0.0.1:5000")
MODEL = "gemini-2.0-flash"
APP_NAME = "mcp_toolbox_poc"
USER_ID = "default_user"
SESSION_ID = "default_session"

# Agent instructions
AGENT_INSTRUCTION = """\
You are a helpful data analyst assistant with access to a PostgreSQL database.

AVAILABLE TOOLS:
Schema exploration:
- list-tables: See all tables and row counts
- describe-table: Get column details for a specific table

Customer data:
- get-customers: List customers (can filter by city/country)
- get-customer-by-id: Get specific customer details
- get-top-customers: See top customers by spend

Order data:
- get-orders: List orders (can filter by status)
- get-order-details: Get full order with line items

Product data:
- get-products: List products (can filter by category)
- get-low-stock-products: Find products below stock threshold

Analytics:
- get-revenue-by-status: Revenue breakdown by order status
- get-sales-by-category: Sales by product category

Custom:
- run-query: Execute custom SELECT queries

GUIDELINES:
1. Use the most specific tool for the task
2. For complex questions, you may need multiple tool calls
3. Always interpret results for the user in plain language
4. If a tool doesn't exist for a query, use run-query with a SELECT statement
"""


def create_agent(toolset_name: str = "all-tools"):
    """
    Create an ADK agent connected to MCP Toolbox.

    Args:
        toolset_name: Name of the toolset to load from tools.yaml

    Returns:
        Configured Agent instance
    """
    # Connect to Toolbox server
    toolbox = ToolboxSyncClient(TOOLBOX_URL)

    # Load tools from the specified toolset
    tools = toolbox.load_toolset(toolset_name)

    print(f"Loaded {len(tools)} tools from '{toolset_name}' toolset")
    for tool in tools:
        print(f"  - {tool.name}")
    print()

    # Create agent with tools
    agent = Agent(
        model=MODEL,
        name="postgres_analyst",
        description="Data analyst agent for PostgreSQL databases",
        instruction=AGENT_INSTRUCTION,
        tools=tools,
    )

    return agent


# Session management
_session_service = InMemorySessionService()


async def _ensure_session():
    """Ensure session exists."""
    try:
        await _session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
    except Exception:
        await _session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )


def query(question: str, toolset: str = "all-tools") -> str:
    """
    Ask a question about the database.

    Args:
        question: Natural language question
        toolset: Which toolset to use

    Returns:
        Agent's response
    """
    asyncio.run(_ensure_session())

    agent = create_agent(toolset)
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=_session_service
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=question)]
    )

    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    )

    response = ""
    for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                response = event.content.parts[0].text

    return response


def interactive_mode():
    """Run the agent interactively."""
    print("\n" + "=" * 60)
    print("MCP Toolbox Agent - PostgreSQL + Gemini")
    print("=" * 60)
    print(f"Connected to Toolbox at: {TOOLBOX_URL}")
    print("Commands: 'quit' to exit, 'tools' to list available tools\n")

    asyncio.run(_ensure_session())

    agent = create_agent("all-tools")
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=_session_service
    )

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue

        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if question.lower() == "tools":
            toolbox = ToolboxSyncClient(TOOLBOX_URL)
            tools = toolbox.load_toolset("all-tools")
            print("\nAvailable tools:")
            for tool in tools:
                print(f"  - {tool.name}")
            print()
            continue

        content = types.Content(
            role="user",
            parts=[types.Part(text=question)]
        )

        events = runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        )

        for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(f"\nAgent: {event.content.parts[0].text}\n")


if __name__ == "__main__":
    interactive_mode()
