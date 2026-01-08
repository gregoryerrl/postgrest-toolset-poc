# POC 3: PGMCP - Natural Language Postgres MCP Server

## Objective

Build and test PGMCP, an open-source MCP server specifically designed for natural language PostgreSQL querying. This is the most purpose-built solution for the use case.

---

## Project Configuration

**Project root:** `poc-pgmcp/`

**Requirements:**
- Go 1.21+ (for building PGMCP)
- PostgreSQL database
- OpenAI API key (PGMCP uses OpenAI for NL-to-SQL)

**Environment variables required:**
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — OpenAI API key (required by PGMCP)
- `GOOGLE_API_KEY` — Gemini API key (for ADK agent wrapper, optional)

---

## File Structure

```
poc-pgmcp/
├── agent/
│   ├── __init__.py
│   └── agent.py
├── scripts/
│   ├── install_pgmcp.sh
│   ├── run_pgmcp.sh
│   └── setup_sample_db.sql
├── tests/
│   ├── __init__.py
│   ├── test_pgmcp_client.py
│   └── test_mcp_integration.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Create file: requirements.txt

```txt
# For Python client/wrapper
httpx>=0.25.0
python-dotenv>=1.0.0
pytest>=7.4.0

# Optional: ADK wrapper
google-adk>=1.1.0
google-genai>=1.0.0
```

---

## Create file: .env.example

```bash
# PostgreSQL Connection (required)
DATABASE_URL=postgres://postgres:postgres@localhost:5432/testdb

# OpenAI API Key (required by PGMCP for NL-to-SQL)
OPENAI_API_KEY=your-openai-api-key-here

# PGMCP Server Configuration
PGMCP_HOST=localhost
PGMCP_PORT=8080

# Optional: Gemini API for ADK wrapper
GOOGLE_API_KEY=your-gemini-api-key-here
```

---

## Create file: scripts/install_pgmcp.sh

```bash
#!/bin/bash

# Install PGMCP from source

set -e

echo "Installing PGMCP..."

# Check for Go
if ! command -v go &> /dev/null; then
    echo "Go is required. Please install Go 1.21+ first."
    echo "  macOS: brew install go"
    echo "  Ubuntu: sudo apt install golang-go"
    exit 1
fi

# Clone repository
if [ ! -d "pgmcp" ]; then
    git clone https://github.com/subnetmarco/pgmcp.git
fi

cd pgmcp

# Build server and client
echo "Building PGMCP server..."
go build -o ../bin/pgmcp-server ./server

echo "Building PGMCP client..."
go build -o ../bin/pgmcp-client ./client

cd ..

echo ""
echo "PGMCP installed successfully!"
echo "  Server: ./bin/pgmcp-server"
echo "  Client: ./bin/pgmcp-client"
```

---

## Create file: scripts/run_pgmcp.sh

```bash
#!/bin/bash

# Run PGMCP server

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required env vars
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is required"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is required"
    exit 1
fi

# Check if binary exists
if [ ! -f ./bin/pgmcp-server ]; then
    echo "PGMCP not found. Running install script..."
    ./scripts/install_pgmcp.sh
fi

echo "Starting PGMCP server..."
echo "Database: $DATABASE_URL"
echo "API: http://localhost:${PGMCP_PORT:-8080}"
echo ""

# Run server
./bin/pgmcp-server
```

---

## Create file: scripts/setup_sample_db.sql

```sql
-- Sample database setup for PGMCP POC
-- Run: psql $DATABASE_URL -f scripts/setup_sample_db.sql

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
    ('Eve Davis', 'eve@example.com', 'Phoenix', 'USA'),
    ('Frank Miller', 'frank@example.com', 'Seattle', 'USA'),
    ('Grace Lee', 'grace@example.com', 'Boston', 'USA');

INSERT INTO products (name, category, price, stock_quantity) VALUES
    ('Laptop Pro 15', 'Electronics', 1299.99, 50),
    ('Wireless Mouse', 'Electronics', 29.99, 200),
    ('USB-C Hub', 'Electronics', 49.99, 150),
    ('Mechanical Keyboard', 'Electronics', 149.99, 75),
    ('Monitor 27"', 'Electronics', 399.99, 30),
    ('Office Chair', 'Furniture', 299.99, 40),
    ('Standing Desk', 'Furniture', 599.99, 25),
    ('Desk Lamp', 'Furniture', 39.99, 100),
    ('Notebook Set', 'Office Supplies', 12.99, 500),
    ('Pen Pack', 'Office Supplies', 8.99, 1000);

INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
    (1, NOW() - INTERVAL '60 days', 'completed', 1329.98),
    (1, NOW() - INTERVAL '30 days', 'completed', 299.99),
    (2, NOW() - INTERVAL '45 days', 'completed', 629.98),
    (2, NOW() - INTERVAL '15 days', 'completed', 149.99),
    (3, NOW() - INTERVAL '20 days', 'shipped', 449.98),
    (4, NOW() - INTERVAL '10 days', 'shipped', 29.99),
    (5, NOW() - INTERVAL '5 days', 'pending', 1299.99),
    (6, NOW() - INTERVAL '3 days', 'pending', 599.99),
    (7, NOW() - INTERVAL '1 day', 'pending', 49.99);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1299.99), (1, 2, 1, 29.99),
    (2, 6, 1, 299.99),
    (3, 7, 1, 599.99), (3, 2, 1, 29.99),
    (4, 4, 1, 149.99),
    (5, 5, 1, 399.99), (5, 3, 1, 49.99),
    (6, 2, 1, 29.99),
    (7, 1, 1, 1299.99),
    (8, 7, 1, 599.99),
    (9, 3, 1, 49.99);

-- Verify
SELECT 'Setup complete!' as status,
       (SELECT COUNT(*) FROM customers) as customers,
       (SELECT COUNT(*) FROM products) as products,
       (SELECT COUNT(*) FROM orders) as orders;
```

---

## Create file: agent/__init__.py

```python
"""PGMCP Python client and ADK wrapper."""

from .agent import PGMCPClient, query, interactive_mode

__all__ = ["PGMCPClient", "query", "interactive_mode"]
```

---

## Create file: agent/agent.py

```python
"""
PGMCP Python Client

A Python wrapper for the PGMCP MCP server that enables natural language
queries against PostgreSQL databases.
"""

import os
import json
from typing import Optional, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

# Configuration
PGMCP_HOST = os.getenv("PGMCP_HOST", "localhost")
PGMCP_PORT = os.getenv("PGMCP_PORT", "8080")
PGMCP_URL = f"http://{PGMCP_HOST}:{PGMCP_PORT}"


class PGMCPClient:
    """
    Python client for PGMCP MCP server.
    
    Provides methods to query PostgreSQL using natural language.
    """
    
    def __init__(self, base_url: str = PGMCP_URL):
        """
        Initialize PGMCP client.
        
        Args:
            base_url: PGMCP server URL (default: http://localhost:8080)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)
    
    def ask(self, question: str, format: str = "json") -> dict[str, Any]:
        """
        Ask a natural language question about the database.
        
        Args:
            question: Natural language question
            format: Response format ('json', 'table', 'csv')
        
        Returns:
            Dict with query results, generated SQL, and any errors
        """
        try:
            response = self.client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "ask",
                        "arguments": {
                            "question": question,
                            "format": format
                        }
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "question": question
                }
            
            return {
                "success": True,
                "result": result.get("result", {}),
                "question": question
            }
            
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def search(self, query: str, limit: int = 100) -> dict[str, Any]:
        """
        Free-text search across all text columns in the database.
        
        Args:
            query: Search term
            limit: Maximum results to return
        
        Returns:
            Dict with search results
        """
        try:
            response = self.client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "search",
                        "arguments": {
                            "query": query,
                            "limit": limit
                        }
                    }
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return {"success": False, "error": str(e)}
    
    def get_schema(self) -> dict[str, Any]:
        """
        Get the database schema.
        
        Returns:
            Dict with table and column information
        """
        try:
            response = self.client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "resources/list",
                    "params": {}
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> bool:
        """Check if PGMCP server is running."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def query(question: str) -> str:
    """
    Quick query function for one-off questions.
    
    Args:
        question: Natural language question
    
    Returns:
        Formatted response string
    """
    with PGMCPClient() as client:
        if not client.health_check():
            return "Error: PGMCP server is not running. Start it with ./scripts/run_pgmcp.sh"
        
        result = client.ask(question)
        
        if not result["success"]:
            return f"Error: {result['error']}"
        
        # Format response
        data = result.get("result", {})
        if isinstance(data, dict) and "content" in data:
            content = data["content"]
            if isinstance(content, list) and content:
                return content[0].get("text", str(data))
        
        return json.dumps(data, indent=2, default=str)


def interactive_mode():
    """Run PGMCP client in interactive mode."""
    print("\n" + "=" * 60)
    print("PGMCP - Natural Language PostgreSQL Queries")
    print("=" * 60)
    print(f"Server: {PGMCP_URL}")
    print("Commands:")
    print("  'quit' - Exit")
    print("  'schema' - Show database schema")
    print("  'search <term>' - Free-text search")
    print("=" * 60 + "\n")
    
    with PGMCPClient() as client:
        if not client.health_check():
            print("Error: PGMCP server is not running!")
            print("Start it with: ./scripts/run_pgmcp.sh")
            return
        
        print("Connected to PGMCP server.\n")
        
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
            
            if user_input.lower() == "schema":
                schema = client.get_schema()
                print(f"\n{json.dumps(schema, indent=2)}\n")
                continue
            
            if user_input.lower().startswith("search "):
                term = user_input[7:].strip()
                results = client.search(term)
                print(f"\n{json.dumps(results, indent=2)}\n")
                continue
            
            # Natural language query
            result = client.ask(user_input)
            
            if result["success"]:
                data = result.get("result", {})
                if isinstance(data, dict) and "content" in data:
                    content = data["content"]
                    if isinstance(content, list) and content:
                        print(f"\nAgent: {content[0].get('text', str(data))}\n")
                    else:
                        print(f"\nAgent: {json.dumps(data, indent=2)}\n")
                else:
                    print(f"\nAgent: {json.dumps(data, indent=2)}\n")
            else:
                print(f"\nError: {result['error']}\n")


# CLI client using the PGMCP binary
def cli_query(question: str) -> str:
    """
    Query using the PGMCP CLI client binary.
    
    This is an alternative to the HTTP client that uses the compiled
    PGMCP client directly.
    """
    import subprocess
    
    result = subprocess.run(
        ["./bin/pgmcp-client", "-ask", question, "-format", "table"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    
    return result.stdout


if __name__ == "__main__":
    interactive_mode()
```

---

## Create file: tests/__init__.py

```python
"""Tests for PGMCP POC."""
```

---

## Create file: tests/test_pgmcp_client.py

```python
"""Tests for PGMCP Python client."""

import pytest
from agent.agent import PGMCPClient, query


class TestPGMCPClient:
    """Test cases for PGMCP client."""
    
    @pytest.fixture
    def client(self):
        """Create client instance."""
        return PGMCPClient()
    
    def test_client_initializes(self, client):
        """Test client initialization."""
        assert client is not None
        assert client.base_url == "http://localhost:8080"
    
    def test_health_check(self, client):
        """Test server health check."""
        # This will fail if server isn't running, which is expected
        result = client.health_check()
        assert isinstance(result, bool)
    
    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_ask_simple_question(self, client):
        """Test asking a simple question."""
        result = client.ask("What tables are in the database?")
        assert "success" in result
    
    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_ask_count_query(self, client):
        """Test a count query."""
        result = client.ask("How many customers are there?")
        assert "success" in result
    
    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_search(self, client):
        """Test free-text search."""
        result = client.search("Alice")
        assert isinstance(result, dict)
    
    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_get_schema(self, client):
        """Test schema retrieval."""
        result = client.get_schema()
        assert isinstance(result, dict)


class TestQueryFunction:
    """Test the convenience query function."""
    
    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_query_returns_string(self):
        """Test that query returns a string."""
        result = query("What tables exist?")
        assert isinstance(result, str)
```

---

## Create file: README.md

```markdown
# POC 3: PGMCP - Natural Language PostgreSQL MCP Server

PGMCP is a purpose-built MCP server for querying PostgreSQL databases using natural language. It's the most specialized solution for this use case.

## Key Features

- **Natural Language to SQL**: Converts questions to SQL using OpenAI
- **Auto-pagination**: Handles large result sets automatically
- **Streaming**: Efficient streaming for large queries
- **Read-only**: Enforces read-only queries for safety
- **MCP Compatible**: Works with Claude Desktop, Cursor, VS Code
- **Free-text Search**: Search across all text columns

## Requirements

- Go 1.21+ (for building PGMCP)
- PostgreSQL database
- OpenAI API key (PGMCP uses OpenAI for NL-to-SQL)

## Quick Start

```bash
# Setup
cd poc-pgmcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENAI_API_KEY

# Install PGMCP
chmod +x scripts/install_pgmcp.sh
./scripts/install_pgmcp.sh

# Setup sample database
psql $DATABASE_URL -f scripts/setup_sample_db.sql

# Start PGMCP server (Terminal 1)
./scripts/run_pgmcp.sh

# Use Python client (Terminal 2)
python -m agent.agent

# Or use CLI client directly
./bin/pgmcp-client -ask "How many customers are there?" -format table
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Python Client  │────▶│  PGMCP Server   │────▶│   PostgreSQL    │
│  or CLI Client  │     │  (Go + OpenAI)  │     │   Database      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## MCP Tools

PGMCP exposes these MCP tools:

| Tool | Description |
|------|-------------|
| `ask` | Natural language questions → SQL queries |
| `search` | Free-text search across all text columns |
| `stream` | Streaming for large result sets |

## IDE Integration

### Claude Desktop

Add to `~/.config/claude-desktop/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pgmcp": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8080/mcp"
      }
    }
  }
}
```

### VS Code / Cursor

Add to `.vscode/mcp.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "pgmcp": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8080/mcp"
      }
    }
  }
}
```

## Pros & Cons

**Pros:**
- Purpose-built for NL-to-SQL on Postgres
- Excellent streaming and pagination
- MCP-native (works with many clients)
- Read-only enforcement

**Cons:**
- Requires OpenAI API key (not Gemini)
- Requires Go to build
- Additional server to run

## CLI Examples

```bash
# Ask questions
./bin/pgmcp-client -ask "Who are the top 5 customers by order value?" -format table

# Search across all text
./bin/pgmcp-client -search "Alice" -format json

# Get help
./bin/pgmcp-client -help
```
```

---

## Run Commands

```bash
# Navigate to project
cd poc-pgmcp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with DATABASE_URL and OPENAI_API_KEY

# Install PGMCP (requires Go)
chmod +x scripts/install_pgmcp.sh
./scripts/install_pgmcp.sh

# Start local Postgres (if using Docker)
docker run -d --name postgres-pgmcp \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:16

# Wait for Postgres, then setup sample data
sleep 5
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/testdb"
psql $DATABASE_URL -f scripts/setup_sample_db.sql

# Terminal 1: Start PGMCP server
chmod +x scripts/run_pgmcp.sh
./scripts/run_pgmcp.sh

# Terminal 2: Test with CLI
./bin/pgmcp-client -ask "What tables are in the database?" -format table

# Or use Python client
python -m agent.agent

# Run tests (with server running)
pytest tests/ -v
```

---

## Test Queries to Try

```bash
# CLI examples
./bin/pgmcp-client -ask "How many customers are there?" -format table
./bin/pgmcp-client -ask "Who placed the most orders?" -format table
./bin/pgmcp-client -ask "What's the total revenue?" -format table
./bin/pgmcp-client -search "Electronics" -format json

# Python interactive mode
python -m agent.agent
# Then ask:
# What tables are in the database?
# Show me all customers from New York
# What are the top selling products?
# Which orders are still pending?
```
