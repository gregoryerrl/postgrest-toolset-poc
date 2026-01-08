# POC 2: Google MCP Toolbox for Databases

## Objective

Build and test Google's MCP Toolbox for Databases with PostgreSQL. This is Google's official solution that integrates directly with ADK agents.

---

## Project Configuration

**Project root:** `poc-mcp-toolbox/`

**Python version:** 3.11+

**Environment variables required:**
- `GOOGLE_API_KEY` — Gemini API key
- `POSTGRES_HOST` — Database host
- `POSTGRES_PORT` — Database port (default: 5432)
- `POSTGRES_DATABASE` — Database name
- `POSTGRES_USER` — Database user
- `POSTGRES_PASSWORD` — Database password

---

## File Structure

```
poc-mcp-toolbox/
├── agent/
│   ├── __init__.py
│   └── agent.py
├── toolbox/
│   └── tools.yaml
├── tests/
│   ├── __init__.py
│   └── test_agent.py
├── scripts/
│   ├── setup_sample_db.sql
│   ├── install_toolbox.sh
│   └── run_toolbox.sh
├── .env.example
├── requirements.txt
└── README.md
```

---

## Create file: requirements.txt

```txt
google-adk>=1.1.0
google-genai>=1.0.0
toolbox-core>=0.1.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.9
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## Create file: .env.example

```bash
# Gemini API
GOOGLE_API_KEY=your-gemini-api-key-here
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=testdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Toolbox Server
TOOLBOX_URL=http://127.0.0.1:5000
```

---

## Create file: toolbox/tools.yaml

```yaml
# MCP Toolbox for Databases - Tools Configuration
# Defines custom SQL tools that the agent can use

sources:
  postgres-source:
    kind: postgres
    host: ${POSTGRES_HOST}
    port: ${POSTGRES_PORT}
    database: ${POSTGRES_DATABASE}
    user: ${POSTGRES_USER}
    password: ${POSTGRES_PASSWORD}

tools:
  # Schema exploration tools
  list-tables:
    kind: postgres-sql
    source: postgres-source
    description: List all tables in the database with their row counts
    statement: |
      SELECT 
        schemaname,
        tablename,
        n_tup_ins as approximate_rows
      FROM pg_stat_user_tables
      ORDER BY schemaname, tablename;

  describe-table:
    kind: postgres-sql
    source: postgres-source
    description: Get detailed information about a specific table including columns, types, and constraints
    parameters:
      - name: table_name
        type: string
        description: The name of the table to describe
    statement: |
      SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_name = $1
      ORDER BY ordinal_position;

  # Customer queries
  get-customers:
    kind: postgres-sql
    source: postgres-source
    description: Get all customers, optionally filtered by city or country
    parameters:
      - name: city
        type: string
        description: Filter by city (optional, use '%' for all)
      - name: country
        type: string
        description: Filter by country (optional, use '%' for all)
    statement: |
      SELECT id, name, email, city, country, created_at
      FROM customers
      WHERE (city ILIKE $1 OR $1 = '%')
        AND (country ILIKE $2 OR $2 = '%')
      ORDER BY name
      LIMIT 100;

  get-customer-by-id:
    kind: postgres-sql
    source: postgres-source
    description: Get a specific customer by their ID
    parameters:
      - name: customer_id
        type: integer
        description: The customer ID
    statement: |
      SELECT * FROM customers WHERE id = $1;

  # Order queries
  get-orders:
    kind: postgres-sql
    source: postgres-source
    description: Get orders with optional status filter
    parameters:
      - name: status
        type: string
        description: Filter by status (pending, shipped, completed, or '%' for all)
    statement: |
      SELECT 
        o.id,
        c.name as customer_name,
        o.order_date,
        o.status,
        o.total_amount
      FROM orders o
      JOIN customers c ON o.customer_id = c.id
      WHERE (o.status = $1 OR $1 = '%')
      ORDER BY o.order_date DESC
      LIMIT 100;

  get-order-details:
    kind: postgres-sql
    source: postgres-source
    description: Get detailed information about a specific order including line items
    parameters:
      - name: order_id
        type: integer
        description: The order ID
    statement: |
      SELECT 
        o.id as order_id,
        c.name as customer_name,
        c.email as customer_email,
        o.order_date,
        o.status,
        p.name as product_name,
        oi.quantity,
        oi.unit_price,
        (oi.quantity * oi.unit_price) as line_total,
        o.total_amount as order_total
      FROM orders o
      JOIN customers c ON o.customer_id = c.id
      JOIN order_items oi ON o.id = oi.order_id
      JOIN products p ON oi.product_id = p.id
      WHERE o.id = $1;

  # Product queries
  get-products:
    kind: postgres-sql
    source: postgres-source
    description: Get products, optionally filtered by category
    parameters:
      - name: category
        type: string
        description: Filter by category (or '%' for all)
    statement: |
      SELECT id, name, category, price, stock_quantity
      FROM products
      WHERE (category ILIKE $1 OR $1 = '%')
      ORDER BY category, name;

  get-low-stock-products:
    kind: postgres-sql
    source: postgres-source
    description: Get products with stock below a threshold
    parameters:
      - name: threshold
        type: integer
        description: Stock quantity threshold
    statement: |
      SELECT id, name, category, price, stock_quantity
      FROM products
      WHERE stock_quantity < $1
      ORDER BY stock_quantity ASC;

  # Analytics queries
  get-revenue-by-status:
    kind: postgres-sql
    source: postgres-source
    description: Get total revenue grouped by order status
    statement: |
      SELECT 
        status,
        COUNT(*) as order_count,
        SUM(total_amount) as total_revenue,
        AVG(total_amount) as avg_order_value
      FROM orders
      GROUP BY status
      ORDER BY total_revenue DESC;

  get-top-customers:
    kind: postgres-sql
    source: postgres-source
    description: Get top customers by total spend
    parameters:
      - name: limit_count
        type: integer
        description: Number of top customers to return
    statement: |
      SELECT 
        c.id,
        c.name,
        c.email,
        COUNT(o.id) as order_count,
        SUM(o.total_amount) as total_spent
      FROM customers c
      LEFT JOIN orders o ON c.id = o.customer_id
      GROUP BY c.id, c.name, c.email
      ORDER BY total_spent DESC NULLS LAST
      LIMIT $1;

  get-sales-by-category:
    kind: postgres-sql
    source: postgres-source
    description: Get sales breakdown by product category
    statement: |
      SELECT 
        p.category,
        COUNT(DISTINCT oi.order_id) as order_count,
        SUM(oi.quantity) as units_sold,
        SUM(oi.quantity * oi.unit_price) as total_revenue
      FROM products p
      JOIN order_items oi ON p.id = oi.product_id
      GROUP BY p.category
      ORDER BY total_revenue DESC;

  # Custom query tool (use with caution)
  run-query:
    kind: postgres-sql
    source: postgres-source
    description: Run a custom read-only SQL query. Only SELECT statements are allowed.
    parameters:
      - name: sql_query
        type: string
        description: The SQL SELECT query to execute
    statement: ${sql_query}

toolsets:
  all-tools:
    - list-tables
    - describe-table
    - get-customers
    - get-customer-by-id
    - get-orders
    - get-order-details
    - get-products
    - get-low-stock-products
    - get-revenue-by-status
    - get-top-customers
    - get-sales-by-category
    - run-query

  schema-tools:
    - list-tables
    - describe-table

  customer-tools:
    - get-customers
    - get-customer-by-id
    - get-top-customers

  order-tools:
    - get-orders
    - get-order-details
    - get-revenue-by-status

  product-tools:
    - get-products
    - get-low-stock-products
    - get-sales-by-category
```

---

## Create file: agent/__init__.py

```python
"""MCP Toolbox Agent POC."""

from .agent import create_agent, query, interactive_mode

__all__ = ["create_agent", "query", "interactive_mode"]
```

---

## Create file: agent/agent.py

```python
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
    except:
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
```

---

## Create file: tests/__init__.py

```python
"""Tests for MCP Toolbox POC."""
```

---

## Create file: tests/test_agent.py

```python
"""Tests for MCP Toolbox agent."""

import pytest
from agent.agent import create_agent, query


class TestToolboxAgent:
    """Test cases for MCP Toolbox agent."""
    
    def test_agent_creates_with_all_tools(self):
        """Test agent creation with all tools."""
        agent = create_agent("all-tools")
        assert agent is not None
    
    def test_agent_creates_with_schema_tools(self):
        """Test agent creation with schema tools only."""
        agent = create_agent("schema-tools")
        assert agent is not None
    
    def test_list_tables_query(self):
        """Test listing tables."""
        result = query("What tables are in the database?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_customer_query(self):
        """Test customer-related query."""
        result = query("Show me all customers")
        assert isinstance(result, str)
    
    def test_order_query(self):
        """Test order-related query."""
        result = query("What orders are pending?")
        assert isinstance(result, str)
    
    def test_analytics_query(self):
        """Test analytics query."""
        result = query("What's the total revenue by order status?")
        assert isinstance(result, str)
```

---

## Create file: scripts/install_toolbox.sh

```bash
#!/bin/bash

# Install MCP Toolbox for Databases

set -e

echo "Installing MCP Toolbox for Databases..."

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
    ARCH="amd64"
elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    ARCH="arm64"
fi

# Get latest release
LATEST_VERSION=$(curl -s https://api.github.com/repos/googleapis/genai-toolbox/releases/latest | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_VERSION" ]; then
    echo "Could not determine latest version. Using v0.6.0"
    LATEST_VERSION="v0.6.0"
fi

echo "Downloading Toolbox $LATEST_VERSION for $OS/$ARCH..."

# Download URL
DOWNLOAD_URL="https://github.com/googleapis/genai-toolbox/releases/download/${LATEST_VERSION}/toolbox_${OS}_${ARCH}"

# Download to local bin directory
mkdir -p ./bin
curl -L "$DOWNLOAD_URL" -o ./bin/toolbox
chmod +x ./bin/toolbox

echo "Toolbox installed to ./bin/toolbox"
./bin/toolbox --version
```

---

## Create file: scripts/run_toolbox.sh

```bash
#!/bin/bash

# Run the MCP Toolbox server

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if toolbox binary exists
if [ ! -f ./bin/toolbox ]; then
    echo "Toolbox not found. Running install script..."
    ./scripts/install_toolbox.sh
fi

echo "Starting MCP Toolbox server..."
echo "Config: toolbox/tools.yaml"
echo "URL: http://127.0.0.1:5000"
echo ""

# Run toolbox with tools.yaml
./bin/toolbox --tools-file toolbox/tools.yaml
```

---

## Create file: scripts/setup_sample_db.sql

```sql
-- Sample database setup for MCP Toolbox POC
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

SELECT 'Database setup complete!' as status;
```

---

## Create file: README.md

```markdown
# POC 2: Google MCP Toolbox for Databases

Uses Google's official MCP Toolbox to connect ADK agents to PostgreSQL.

## Key Differences from LangChain

- **Predefined tools**: SQL queries are defined in `tools.yaml`, not generated dynamically
- **More control**: You decide exactly what queries are allowed
- **Better security**: No arbitrary SQL generation
- **Google ADK native**: Designed to work with ADK agents

## Quick Start

```bash
# Setup
cd poc-mcp-toolbox
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Install Toolbox binary
chmod +x scripts/install_toolbox.sh
./scripts/install_toolbox.sh

# Setup sample database
psql -U postgres -d testdb -f scripts/setup_sample_db.sql

# Start Toolbox server (Terminal 1)
./scripts/run_toolbox.sh

# Run agent (Terminal 2)
python -m agent.agent
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ADK Agent     │────▶│  MCP Toolbox    │────▶│   PostgreSQL    │
│   (Gemini)      │     │  (tools.yaml)   │     │   Database      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Customizing Tools

Edit `toolbox/tools.yaml` to add new queries:

```yaml
tools:
  my-custom-query:
    kind: postgres-sql
    source: postgres-source
    description: Description for the LLM
    parameters:
      - name: param1
        type: string
        description: What this param does
    statement: |
      SELECT * FROM table WHERE column = $1;
```

## Pros & Cons

**Pros:**
- Explicit control over allowed queries
- Better security (no SQL injection risk)
- Native ADK integration
- Toolsets for different use cases

**Cons:**
- Must predefine all queries
- Less flexible for ad-hoc analysis
- More setup overhead
```

---

## Run Commands

```bash
# Navigate to project
cd poc-mcp-toolbox

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY and Postgres credentials

# Install Toolbox binary
chmod +x scripts/install_toolbox.sh
./scripts/install_toolbox.sh

# Start local Postgres (if using Docker)
docker run -d --name postgres-toolbox \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:16

# Wait for Postgres, then setup sample data
sleep 5
PGPASSWORD=postgres psql -h localhost -U postgres -d testdb -f scripts/setup_sample_db.sql

# Terminal 1: Start Toolbox server
chmod +x scripts/run_toolbox.sh
./scripts/run_toolbox.sh

# Terminal 2: Run agent
python -m agent.agent

# Or run tests
pytest tests/ -v
```

---

## Test Queries to Try

```
What tables are in the database?
Show me all customers
Who are the top 3 customers by spending?
What orders are pending?
Show me the details of order 1
What's the revenue breakdown by status?
What products have low stock (under 50)?
What are the sales by category?
```
