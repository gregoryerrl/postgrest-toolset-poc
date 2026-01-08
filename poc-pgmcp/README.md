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
