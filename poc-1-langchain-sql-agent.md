# POC 1: LangChain SQL Agent for Postgres

## Objective

Build and test LangChain's `create_sql_agent` with PostgreSQL and Gemini. This is the most mature text-to-SQL solution with built-in error recovery.

---

## Project Configuration

**Project root:** `poc-langchain-sql-agent/`

**Python version:** 3.11+

**Environment variables required:**
- `GOOGLE_API_KEY` — Gemini API key
- `POSTGRES_URI` — PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/dbname`)

---

## File Structure

```
poc-langchain-sql-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   └── test_agent.py
├── scripts/
│   └── setup_sample_db.sql
├── .env.example
├── requirements.txt
└── README.md
```

---

## Create file: requirements.txt

```txt
langchain>=0.3.0
langchain-community>=0.3.0
langchain-google-genai>=2.0.0
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
# Format: postgresql://username:password@host:port/database
POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/testdb
```

---

## Create file: src/__init__.py

```python
"""LangChain SQL Agent POC."""
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
    
    # Validate required config
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    return config
```

---

## Create file: src/agent.py

```python
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
```

---

## Create file: tests/__init__.py

```python
"""Tests for LangChain SQL Agent POC."""
```

---

## Create file: tests/test_agent.py

```python
"""Tests for the LangChain SQL agent."""

import pytest
from src.agent import create_postgres_agent, query


class TestSQLAgent:
    """Test cases for SQL agent functionality."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return create_postgres_agent(verbose=False)
    
    def test_agent_creates_successfully(self, agent):
        """Test that agent initializes without error."""
        assert agent is not None
    
    def test_list_tables(self, agent):
        """Test that agent can list tables."""
        result = agent.invoke({"input": "What tables are in the database?"})
        assert "output" in result
        assert len(result["output"]) > 0
    
    def test_simple_count_query(self, agent):
        """Test a simple count query."""
        result = agent.invoke({"input": "How many tables are in the database?"})
        assert "output" in result
    
    def test_schema_description(self, agent):
        """Test getting schema information."""
        result = agent.invoke({"input": "Describe the schema of the database"})
        assert "output" in result
    
    def test_query_function(self):
        """Test the convenience query function."""
        result = query("What tables exist?", verbose=False)
        assert isinstance(result, str)
        assert len(result) > 0


class TestErrorHandling:
    """Test error handling capabilities."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return create_postgres_agent(verbose=False)
    
    def test_handles_nonexistent_table(self, agent):
        """Test that agent handles queries about nonexistent tables."""
        result = agent.invoke({
            "input": "How many rows are in the xyz_nonexistent_table_123?"
        })
        # Should not crash, should provide helpful response
        assert "output" in result
    
    def test_handles_ambiguous_query(self, agent):
        """Test that agent handles ambiguous queries."""
        result = agent.invoke({"input": "Show me everything"})
        assert "output" in result
```

---

## Create file: scripts/setup_sample_db.sql

```sql
-- Sample database setup for testing LangChain SQL Agent POC
-- Run: psql -U postgres -d testdb -f scripts/setup_sample_db.sql

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

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2)
);

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL
);

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
    (1, 1, 1, 1299.99),
    (1, 2, 1, 29.99),
    (2, 3, 1, 299.99),
    (3, 4, 1, 599.99),
    (3, 2, 1, 29.99),
    (4, 2, 1, 29.99),
    (5, 1, 1, 1299.99);

-- Verify data
SELECT 'customers' AS table_name, COUNT(*) AS rows FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;
```

---

## Create file: README.md

```markdown
# POC 1: LangChain SQL Agent for PostgreSQL

Uses LangChain's `create_sql_agent` with Gemini to query PostgreSQL databases using natural language.

## Features

- Built-in error recovery (retries failed queries)
- Schema exploration tools
- Sample row context for better SQL generation
- Works with any SQLAlchemy-supported database

## Quick Start

```bash
# Setup
cd poc-langchain-sql-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Setup sample database (optional)
psql -U postgres -d testdb -f scripts/setup_sample_db.sql

# Run interactive mode
python -m src.agent

# Run tests
pytest tests/ -v
```

## Example Queries

```
You: What tables are in the database?
You: How many customers do we have?
You: What's the total revenue from completed orders?
You: Who are the top 3 customers by order value?
You: Show me products with low stock (under 50 units)
```

## How It Works

LangChain's SQL agent uses these tools:
- `sql_db_list_tables` - List available tables
- `sql_db_schema` - Get table schemas with sample rows
- `sql_db_query` - Execute SQL queries

The agent automatically:
1. Explores schema when needed
2. Generates SQL based on the question
3. Executes and interprets results
4. Retries on errors with corrections
```

---

## Run Commands

```bash
# Navigate to project
cd poc-langchain-sql-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY and POSTGRES_URI

# Start local Postgres (if using Docker)
docker run -d --name postgres-langchain \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:16

# Wait for Postgres to start, then setup sample data
sleep 5
PGPASSWORD=postgres psql -h localhost -U postgres -d testdb -f scripts/setup_sample_db.sql

# Run tests
pytest tests/ -v

# Run interactive agent
python -m src.agent
```

---

## Test Queries to Try

After starting the agent, test with these queries:

```
What tables are in the database?
Describe the customers table
How many orders are there?
What's the average order value?
Which customer has spent the most?
Show me all pending orders with customer names
What products are in the Electronics category?
```
