# PostgreSQL Natural Language Query POCs

Comparing different approaches for querying PostgreSQL with natural language.

## Overview

| POC | Approach | Status | Best For |
|-----|----------|--------|----------|
| [postgres-toolset](./postgres-toolset/) | ADK Toolset (Gemini) | **Recommended** | ADK integration, minimal tools |
| [poc-langchain-sql-agent](./poc-langchain-sql-agent/) | LangChain (Gemini) | Tested | Quick prototyping |
| [poc-llamaindex-sql](./poc-llamaindex-sql/) | LlamaIndex (Gemini) | Tested | Complex schemas |
| [poc-mcp-toolbox](./poc-mcp-toolbox/) | MCP Toolbox (Gemini) | Requires Go server | Predefined queries |
| [poc-pgmcp](./poc-pgmcp/) | PGMCP (OpenAI) | Requires Go server | MCP clients |

## Recommended: postgres-toolset

Mirrors BigQueryToolset architecture with 5 focused tools:

```python
from postgres_toolset import PostgresToolset, PostgresConfig
from google.adk.agents import Agent

toolset = PostgresToolset(PostgresConfig.from_env())
agent = Agent(model="gemini-2.0-flash", tools=[toolset])
```

Tools: `list_schemas`, `list_tables`, `get_table_info`, `execute_sql`, `ask_data_insights`

## Quick Start

```bash
# 1. Setup database
psql -d testdb -f shared/setup_sample_db.sql

# 2. Set environment
export POSTGRES_URI=postgresql://user@localhost:5432/testdb
export GOOGLE_API_KEY=your-key

# 3. Run any POC
cd postgres-toolset && pip install -e . && python example_agent.py
# or
cd poc-langchain-sql-agent && pip install -r requirements.txt && python -m src.agent
# or
cd poc-llamaindex-sql && pip install -r requirements.txt && python -m src.engine
```

## Sample Queries

- "How many customers do we have?"
- "Who are the top 3 customers by total spend?"
- "What's the total revenue from completed orders?"

## License

MIT
