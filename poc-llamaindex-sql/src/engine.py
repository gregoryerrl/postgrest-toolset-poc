"""
LlamaIndex SQL Query Engine for PostgreSQL.

Uses LlamaIndex's NLSQLTableQueryEngine for natural language to SQL conversion.
"""

from typing import Optional, List
from sqlalchemy import create_engine, inspect

from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.indices.struct_store.sql_query import SQLTableRetrieverQueryEngine
from llama_index.core.objects import SQLTableNodeMapping, ObjectIndex, SQLTableSchema

from .config import get_config, setup_gemini


def get_database_tables(engine) -> List[str]:
    """Get all table names from the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()


def create_sql_database(
    include_tables: Optional[List[str]] = None,
    sample_rows: int = 3
) -> SQLDatabase:
    """
    Create a LlamaIndex SQLDatabase instance.

    Args:
        include_tables: List of tables to include (None = all tables)
        sample_rows: Number of sample rows to include in schema info

    Returns:
        SQLDatabase instance
    """
    config = get_config()

    # Create SQLAlchemy engine
    engine = create_engine(config["postgres_uri"])

    # Get tables if not specified
    if include_tables is None:
        include_tables = get_database_tables(engine)

    # Create LlamaIndex SQL database
    sql_database = SQLDatabase(
        engine=engine,
        include_tables=include_tables,
        sample_rows_in_table_info=sample_rows,
    )

    return sql_database


def create_query_engine(
    include_tables: Optional[List[str]] = None,
    verbose: bool = True
) -> NLSQLTableQueryEngine:
    """
    Create a natural language SQL query engine.

    This is the simplest approach - directly queries tables based on
    the natural language input.

    Args:
        include_tables: Tables to include (None = all)
        verbose: Whether to print verbose output

    Returns:
        NLSQLTableQueryEngine instance
    """
    # Setup Gemini
    llm = setup_gemini()

    # Create SQL database
    sql_database = create_sql_database(include_tables)

    if verbose:
        print("Tables available:")
        for table in sql_database.get_usable_table_names():
            print(f"  - {table}")
        print()

    # Create query engine
    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        llm=llm,
        verbose=verbose,
    )

    return query_engine


def create_retriever_query_engine(
    include_tables: Optional[List[str]] = None,
    verbose: bool = True
) -> SQLTableRetrieverQueryEngine:
    """
    Create a query engine with table retrieval.

    This approach first identifies relevant tables, then queries them.
    Better for databases with many tables.

    Args:
        include_tables: Tables to include (None = all)
        verbose: Whether to print verbose output

    Returns:
        SQLTableRetrieverQueryEngine instance
    """
    from llama_index.core import VectorStoreIndex

    # Setup Gemini
    llm = setup_gemini()

    # Create SQL database
    sql_database = create_sql_database(include_tables)

    # Get table names
    table_names = list(sql_database.get_usable_table_names())

    if verbose:
        print("Building table index...")
        print(f"Tables: {table_names}")
        print()

    # Create table node mapping
    table_node_mapping = SQLTableNodeMapping(sql_database)

    # Create table schema objects with descriptions
    table_schema_objs = []
    for table_name in table_names:
        table_schema_objs.append(
            SQLTableSchema(table_name=table_name)
        )

    # Build object index for table retrieval
    obj_index = ObjectIndex.from_objects(
        table_schema_objs,
        table_node_mapping,
        VectorStoreIndex,
    )

    # Create query engine with retrieval
    query_engine = SQLTableRetrieverQueryEngine(
        sql_database=sql_database,
        table_retriever=obj_index.as_retriever(similarity_top_k=3),
        llm=llm,
        verbose=verbose,
    )

    return query_engine


def query(
    question: str,
    use_retriever: bool = False,
    verbose: bool = True
) -> dict:
    """
    Query the database using natural language.

    Args:
        question: Natural language question
        use_retriever: Whether to use table retrieval (better for many tables)
        verbose: Whether to print verbose output

    Returns:
        Dict with response, SQL query, and metadata
    """
    if use_retriever:
        engine = create_retriever_query_engine(verbose=verbose)
    else:
        engine = create_query_engine(verbose=verbose)

    response = engine.query(question)

    return {
        "question": question,
        "answer": str(response),
        "sql": response.metadata.get("sql_query", "N/A"),
        "source_nodes": [
            {
                "text": node.text,
                "score": node.score if hasattr(node, "score") else None
            }
            for node in response.source_nodes
        ] if hasattr(response, "source_nodes") else []
    }


def interactive_mode():
    """Run the query engine interactively."""
    print("\n" + "=" * 60)
    print("LlamaIndex SQL Query Engine - PostgreSQL + Gemini")
    print("=" * 60)
    print("Commands:")
    print("  'quit' - Exit")
    print("  'tables' - List available tables")
    print("  'schema <table>' - Show table schema")
    print("  'retriever on/off' - Toggle table retrieval mode")
    print("=" * 60 + "\n")

    use_retriever = False
    sql_database = create_sql_database()

    # Create initial engine
    llm = setup_gemini()
    engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        llm=llm,
        verbose=True,
    )

    print(f"Mode: {'Retriever' if use_retriever else 'Direct'}")
    print(f"Tables: {list(sql_database.get_usable_table_names())}\n")

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

        if user_input.lower() == "tables":
            print("\nAvailable tables:")
            for table in sql_database.get_usable_table_names():
                print(f"  - {table}")
            print()
            continue

        if user_input.lower().startswith("schema "):
            table_name = user_input[7:].strip()
            try:
                info = sql_database.get_single_table_info(table_name)
                print(f"\n{info}\n")
            except Exception as e:
                print(f"\nError: {e}\n")
            continue

        if user_input.lower() == "retriever on":
            use_retriever = True
            engine = create_retriever_query_engine(verbose=True)
            print("Switched to retriever mode\n")
            continue

        if user_input.lower() == "retriever off":
            use_retriever = False
            engine = NLSQLTableQueryEngine(
                sql_database=sql_database,
                llm=llm,
                verbose=True,
            )
            print("Switched to direct mode\n")
            continue

        # Query the database
        try:
            response = engine.query(user_input)
            print(f"\nAnswer: {response}")
            if hasattr(response, "metadata") and "sql_query" in response.metadata:
                print(f"SQL: {response.metadata['sql_query']}")
            print()
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    interactive_mode()
