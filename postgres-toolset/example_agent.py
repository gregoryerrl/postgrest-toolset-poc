"""Example ADK Agent using PostgresToolset.

Demonstrates how to use PostgresToolset with Google ADK,
mirroring how BigQueryToolset is used.
"""

import asyncio
import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import our toolset
from src import PostgresToolset, PostgresConfig

load_dotenv()

# Configuration
MODEL = "gemini-2.0-flash"
APP_NAME = "postgres_toolset_demo"
USER_ID = "demo_user"
SESSION_ID = "demo_session"

# Agent instructions - focused and concise
AGENT_INSTRUCTION = """\
You are a data analyst assistant with PostgreSQL database access.

TOOLS:
- list_schemas: Discover available schemas
- list_tables: See tables in a schema
- get_table_info: Get column details for a table
- execute_sql: Run SQL queries
- ask_data_insights: Answer questions in natural language

WORKFLOW:
1. For schema questions: list_schemas → list_tables → get_table_info
2. For data questions: ask_data_insights (handles SQL generation)
3. For specific queries: execute_sql

Keep responses concise and data-focused.
"""


async def create_agent() -> Agent:
    """Create an ADK agent with PostgresToolset."""
    # Create toolset from environment
    config = PostgresConfig.from_env()
    toolset = PostgresToolset(config)

    # Create agent
    agent = Agent(
        model=MODEL,
        name="postgres_analyst",
        description="PostgreSQL data analyst agent",
        instruction=AGENT_INSTRUCTION,
        tools=[toolset],
    )

    return agent


async def query(question: str) -> str:
    """Ask a question and get the response."""
    session_service = InMemorySessionService()

    # Create session
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Create agent and runner
    agent = await create_agent()
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    # Create message
    content = types.Content(
        role="user",
        parts=[types.Part(text=question)]
    )

    # Run and collect response
    response = ""
    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    )

    for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                response = event.content.parts[0].text

    return response


async def interactive_mode():
    """Run in interactive mode."""
    print("\n" + "=" * 60)
    print("PostgresToolset Agent - ADK Demo")
    print("=" * 60)
    print("Commands: 'quit' to exit\n")

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    agent = await create_agent()
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
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
    asyncio.run(interactive_mode())
