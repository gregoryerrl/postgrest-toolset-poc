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
+-------------------+     +-------------------+     +-------------------+
|   ADK Agent       |---->|  MCP Toolbox      |---->|   PostgreSQL      |
|   (Gemini)        |     |  (tools.yaml)     |     |   Database        |
+-------------------+     +-------------------+     +-------------------+
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

## Test Queries

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
