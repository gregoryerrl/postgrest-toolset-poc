"""
LlamaIndex Chat Engine for SQL.

Provides conversational interface with memory for follow-up questions.
"""

from typing import Optional, List

from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.memory import ChatMemoryBuffer

from .engine import create_query_engine, create_retriever_query_engine
from .config import setup_gemini


def create_chat_engine(
    include_tables: Optional[List[str]] = None,
    use_retriever: bool = False,
    memory_token_limit: int = 3000
):
    """
    Create a chat engine with conversation memory.

    This allows for follow-up questions and context-aware responses.

    Args:
        include_tables: Tables to include
        use_retriever: Whether to use table retrieval
        memory_token_limit: Max tokens to keep in memory

    Returns:
        Chat engine instance
    """
    setup_gemini()

    # Create base query engine
    if use_retriever:
        query_engine = create_retriever_query_engine(include_tables, verbose=False)
    else:
        query_engine = create_query_engine(include_tables, verbose=False)

    # Create memory buffer
    memory = ChatMemoryBuffer.from_defaults(token_limit=memory_token_limit)

    # Create chat engine
    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        memory=memory,
        verbose=True,
    )

    return chat_engine


def chat(message: str, chat_engine=None) -> str:
    """
    Send a message to the chat engine.

    Args:
        message: User message
        chat_engine: Existing chat engine (creates new if None)

    Returns:
        Chat response string
    """
    if chat_engine is None:
        chat_engine = create_chat_engine()

    response = chat_engine.chat(message)
    return str(response)


def interactive_chat():
    """Run the chat engine interactively."""
    print("\n" + "=" * 60)
    print("LlamaIndex SQL Chat - PostgreSQL + Gemini")
    print("=" * 60)
    print("This mode supports follow-up questions!")
    print("Commands: 'quit' to exit, 'reset' to clear memory")
    print("=" * 60 + "\n")

    chat_engine = create_chat_engine()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if user_input.lower() == "reset":
            chat_engine = create_chat_engine()
            print("Memory cleared. Starting fresh conversation.\n")
            continue

        try:
            response = chat_engine.chat(user_input)
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    interactive_chat()
