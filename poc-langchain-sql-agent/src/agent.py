"""
LangChain SQL Agent for PostgreSQL with Gemini.

This is the main POC file demonstrating LangChain's SQL agent capabilities.
"""

from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import get_config


def create_postgres_agent(verbose: bool = True):
    """
    Create a LangChain SQL agent connected to PostgreSQL using Gemini.

    Args:
        verbose: Whether to print agent's reasoning steps

    Returns:
        AgentExecutor instance ready to process queries
    """
    config = get_config()

    # Initialize database connection
    db = SQLDatabase.from_uri(
        config["postgres_uri"],
        sample_rows_in_table_info=3,  # Include sample rows in schema info
    )

    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=config["google_api_key"],
        temperature=0,  # Deterministic for SQL generation
    )

    # Create toolkit with database and LLM
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Print available tools for reference
    if verbose:
        print("Available tools:")
        for tool in toolkit.get_tools():
            print(f"  - {tool.name}: {tool.description[:80]}...")
        print()

    # Create the agent
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="openai-tools",  # Works well with Gemini too
        verbose=verbose,
        handle_parsing_errors=True,  # Graceful error handling
    )

    return agent


def query(question: str, verbose: bool = True) -> str:
    """
    Ask a natural language question about the database.

    Args:
        question: Natural language question
        verbose: Whether to print reasoning steps

    Returns:
        Agent's answer as a string
    """
    agent = create_postgres_agent(verbose=verbose)
    result = agent.invoke({"input": question})
    return result["output"]


def interactive_mode():
    """Run the agent in interactive mode."""
    print("\n" + "=" * 60)
    print("LangChain SQL Agent - PostgreSQL + Gemini")
    print("=" * 60)
    print("Commands: 'quit' to exit, 'schema' to see tables\n")

    agent = create_postgres_agent(verbose=True)

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

        if question.lower() == "schema":
            # Quick schema lookup
            result = agent.invoke({"input": "List all tables and their columns"})
        else:
            result = agent.invoke({"input": question})

        print(f"\nAgent: {result['output']}\n")


if __name__ == "__main__":
    interactive_mode()
