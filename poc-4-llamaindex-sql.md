# POC 4: LlamaIndex NLSQLQueryEngine for PostgreSQL

## Objective

Build and test LlamaIndex's NLSQLQueryEngine with PostgreSQL and Gemini. LlamaIndex is known for its schema-aware indexing which can improve SQL generation accuracy.

---

## Project Configuration

**Project root:** `poc-llamaindex-sql/`

**Python version:** 3.11+

**Environment variables required:**
- `GOOGLE_API_KEY` — Gemini API key
- `POSTGRES_URI` — PostgreSQL connection string

---

## File Structure

```
poc-llamaindex-sql/
├── src/
│   ├── __init__.py
│   ├── engine.py
│   ├── config.py
│   └── chat.py
├── tests/
│   ├── __init__.py
│   └── test_engine.py
├── scripts/
│   └── setup_sample_db.sql
├── .env.example
├── requirements.txt
└── README.md
```

---

## Create file: requirements.txt

```txt
llama-index>=0.11.0
llama-index-llms-gemini>=0.3.0
llama-index-embeddings-gemini>=0.2.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
pytest>=7.4.0
```

---

## Create file: .env.example

```bash
# Gemini API
GOOGLE_API_KEY=your-gemini-api-key-here

# PostgreSQL Connection URI
POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/testdb
```

---

## Create file: src/__init__.py

```python
"""LlamaIndex SQL Query Engine POC."""

from .engine import create_query_engine, query
from .chat import create_chat_engine, chat

__all__ = ["create_query_engine", "query", "create_chat_engine", "chat"]
```

---

## Create file: src/config.py

```python
"""Configuration management."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_config():
    """Get configuration from environment variables."""
    config = {
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "postgres_uri": os.getenv("POSTGRES_URI"),
    }
    
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    return config


def setup_gemini():
    """Configure Gemini as the LLM for LlamaIndex."""
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.gemini import GeminiEmbedding
    from llama_index.core import Settings
    
    config = get_config()
    
    # Set up Gemini LLM
    Settings.llm = Gemini(
        api_key=config["google_api_key"],
        model="models/gemini-2.0-flash",
        temperature=0.1,
    )
    
    # Set up Gemini embeddings (for schema indexing)
    Settings.embed_model = GeminiEmbedding(
        api_key=config["google_api_key"],
        model_name="models/text-embedding-004",
    )
    
    return Settings.llm
```

---

## Create file: src/engine.py

```python
"""
LlamaIndex SQL Query Engine for PostgreSQL.

Uses LlamaIndex's NLSQLTableQueryEngine for natural language to SQL conversion.
"""

from typing import Optional, List
from sqlalchemy import create_engine, MetaData, inspect

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
```

---

## Create file: src/chat.py

```python
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
```

---

## Create file: tests/__init__.py

```python
"""Tests for LlamaIndex SQL POC."""
```

---

## Create file: tests/test_engine.py

```python
"""Tests for LlamaIndex SQL query engine."""

import pytest
from src.engine import (
    create_sql_database,
    create_query_engine,
    create_retriever_query_engine,
    query
)
from src.chat import create_chat_engine, chat


class TestSQLDatabase:
    """Test SQL database creation."""
    
    def test_creates_database(self):
        """Test that SQL database is created."""
        db = create_sql_database()
        assert db is not None
    
    def test_has_tables(self):
        """Test that tables are discovered."""
        db = create_sql_database()
        tables = list(db.get_usable_table_names())
        assert len(tables) > 0
    
    def test_can_get_table_info(self):
        """Test getting table information."""
        db = create_sql_database()
        tables = list(db.get_usable_table_names())
        if tables:
            info = db.get_single_table_info(tables[0])
            assert len(info) > 0


class TestQueryEngine:
    """Test query engine functionality."""
    
    def test_creates_query_engine(self):
        """Test query engine creation."""
        engine = create_query_engine(verbose=False)
        assert engine is not None
    
    def test_simple_query(self):
        """Test a simple query."""
        result = query("How many tables are in the database?", verbose=False)
        assert "answer" in result
        assert len(result["answer"]) > 0
    
    def test_count_query(self):
        """Test a count query."""
        result = query("How many customers are there?", verbose=False)
        assert "answer" in result
    
    def test_returns_sql(self):
        """Test that SQL is returned in metadata."""
        result = query("Count all orders", verbose=False)
        assert "sql" in result


class TestRetrieverEngine:
    """Test retriever-based query engine."""
    
    def test_creates_retriever_engine(self):
        """Test retriever engine creation."""
        engine = create_retriever_query_engine(verbose=False)
        assert engine is not None
    
    def test_query_with_retriever(self):
        """Test query using retriever."""
        result = query(
            "What's the total order value?",
            use_retriever=True,
            verbose=False
        )
        assert "answer" in result


class TestChatEngine:
    """Test chat engine with memory."""
    
    def test_creates_chat_engine(self):
        """Test chat engine creation."""
        engine = create_chat_engine()
        assert engine is not None
    
    def test_chat_response(self):
        """Test chat returns response."""
        response = chat("What tables exist?")
        assert isinstance(response, str)
        assert len(response) > 0
```

---

## Create file: scripts/setup_sample_db.sql

```sql
-- Sample database setup for LlamaIndex POC
-- Run: psql $POSTGRES_URI -f scripts/setup_sample_db.sql

-- Clean up existing tables
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'USA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE customers IS 'Store customer information including contact details';
COMMENT ON COLUMN customers.name IS 'Full name of the customer';
COMMENT ON COLUMN customers.email IS 'Email address (unique identifier)';

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0
);

COMMENT ON TABLE products IS 'Product catalog with pricing and inventory';
COMMENT ON COLUMN products.category IS 'Product category (Electronics, Furniture, etc.)';
COMMENT ON COLUMN products.price IS 'Unit price in USD';

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2)
);

COMMENT ON TABLE orders IS 'Customer orders with status tracking';
COMMENT ON COLUMN orders.status IS 'Order status: pending, shipped, completed, cancelled';

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL
);

COMMENT ON TABLE order_items IS 'Line items for each order';

-- Insert sample data
INSERT INTO customers (name, email, city, country) VALUES
    ('Alice Johnson', 'alice@example.com', 'New York', 'USA'),
    ('Bob Smith', 'bob@example.com', 'Los Angeles', 'USA'),
    ('Carol White', 'carol@example.com', 'Chicago', 'USA'),
    ('David Brown', 'david@example.com', 'Houston', 'USA'),
    ('Eve Davis', 'eve@example.com', 'Phoenix', 'USA');

INSERT INTO products (name, category, price, stock_quantity) VALUES
    ('Laptop Pro', 'Electronics', 1299.99, 50),
    ('Wireless Mouse', 'Electronics', 29.99, 200),
    ('Office Chair', 'Furniture', 299.99, 40),
    ('Standing Desk', 'Furniture', 599.99, 25),
    ('Notebook Set', 'Office Supplies', 12.99, 500);

INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
    (1, NOW() - INTERVAL '30 days', 'completed', 1329.98),
    (1, NOW() - INTERVAL '15 days', 'completed', 299.99),
    (2, NOW() - INTERVAL '20 days', 'completed', 629.98),
    (3, NOW() - INTERVAL '10 days', 'shipped', 29.99),
    (4, NOW() - INTERVAL '5 days', 'pending', 1299.99);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1299.99), (1, 2, 1, 29.99),
    (2, 3, 1, 299.99),
    (3, 4, 1, 599.99), (3, 2, 1, 29.99),
    (4, 2, 1, 29.99),
    (5, 1, 1, 1299.99);

SELECT 'Setup complete!' as status;
```

---

## Create file: README.md

```markdown
# POC 4: LlamaIndex NLSQLQueryEngine for PostgreSQL

Uses LlamaIndex's schema-aware SQL query engine with Gemini for natural language database queries.

## Key Features

- **Schema-aware indexing**: LlamaIndex indexes table schemas for better SQL generation
- **Table retrieval**: Can automatically identify relevant tables for complex queries
- **Conversation memory**: Chat mode supports follow-up questions
- **Sample rows**: Includes sample data in context for better understanding

## Quick Start

```bash
# Setup
cd poc-llamaindex-sql
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Setup sample database
psql $POSTGRES_URI -f scripts/setup_sample_db.sql

# Run query engine
python -m src.engine

# Or run chat mode (with memory)
python -m src.chat
```

## Query Modes

### Direct Query Mode
Queries all tables directly. Best for simple databases.

```python
from src.engine import query
result = query("How many customers do we have?")
print(result["answer"])
print(result["sql"])
```

### Retriever Mode
First identifies relevant tables, then queries. Better for complex databases.

```python
from src.engine import query
result = query("What's our best selling product?", use_retriever=True)
```

### Chat Mode
Conversational interface with memory for follow-up questions.

```python
from src.chat import create_chat_engine

chat_engine = create_chat_engine()
response1 = chat_engine.chat("How many orders are there?")
response2 = chat_engine.chat("What about last month?")  # Follows up!
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LlamaIndex                                │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐    ┌───────────────┐    ┌─────────────┐ │
│  │ Schema Index  │───▶│ SQL Generator │───▶│  Executor   │ │
│  │  (Embeddings) │    │   (Gemini)    │    │ (SQLAlchemy)│ │
│  └───────────────┘    └───────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    └─────────────────┘
```

## Pros & Cons

**Pros:**
- Schema-aware (better SQL accuracy)
- Conversation memory in chat mode
- Table retrieval for complex schemas
- Sample rows improve understanding
- Native Gemini support

**Cons:**
- More complex setup than LangChain
- Embedding model required for retriever mode
- Can be slower due to indexing
```

---

## Run Commands

```bash
# Navigate to project
cd poc-llamaindex-sql

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with GOOGLE_API_KEY and POSTGRES_URI

# Start local Postgres (if using Docker)
docker run -d --name postgres-llamaindex \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:16

# Wait for Postgres, then setup sample data
sleep 5
export POSTGRES_URI="postgresql://postgres:postgres@localhost:5432/testdb"
psql $POSTGRES_URI -f scripts/setup_sample_db.sql

# Run tests
pytest tests/ -v

# Run query engine (interactive)
python -m src.engine

# Run chat mode (with memory)
python -m src.chat
```

---

## Test Queries to Try

### Query Mode
```
What tables are in the database?
How many customers are there?
What's the total revenue from completed orders?
Who is the top customer by order value?
Show me all pending orders
What products are in the Electronics category?
```

### Chat Mode (follow-up questions work!)
```
You: How many orders do we have?
Assistant: There are 5 orders...

You: What about just completed ones?
Assistant: There are 3 completed orders...

You: Who placed those?
Assistant: The completed orders were placed by Alice, Bob, and Carol...
```
