# PostgresToolset

A PostgreSQL Toolset for Google ADK that mirrors BigQueryToolset's architecture.

## Overview

PostgresToolset provides 5 focused tools for schema exploration, SQL execution, and natural language insights:

| Tool | Description | BigQuery Equivalent |
|------|-------------|---------------------|
| `list_schemas` | List available schemas | `list_dataset_ids` |
| `list_tables` | List tables in a schema | `list_table_ids` |
| `get_table_info` | Get table metadata | `get_table_info` |
| `execute_sql` | Run SQL queries | `execute_sql` |
| `ask_data_insights` | Natural language to SQL | `ask_data_insights` |

## Design Principles

Based on feedback for minimal, focused tools:

1. **Simplify tool calls** - Only 5 essential tools instead of 12+
2. **Reduce token usage** - Concise responses, no verbose metadata
3. **Schema → SQL → Insights pipeline** - Clear workflow for data exploration

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

```python
from src import PostgresToolset, PostgresConfig
from google.adk.agents import Agent

# Create toolset
config = PostgresConfig(
    connection_string="postgresql://user:pass@localhost:5432/mydb",
)
toolset = PostgresToolset(config)

# Use with ADK agent
agent = Agent(
    model="gemini-2.0-flash",
    tools=[toolset],
)
```

### From Environment

```python
# Uses POSTGRES_URI and GOOGLE_API_KEY from environment
config = PostgresConfig.from_env()
toolset = PostgresToolset(config)
```

### Example Agent

```bash
# Set environment variables
export POSTGRES_URI="postgresql://postgres:postgres@localhost:5432/testdb"
export GOOGLE_API_KEY="your-api-key"

# Run interactive agent
python example_agent.py
```

## Configuration

### PostgresConfig

| Option | Default | Description |
|--------|---------|-------------|
| `connection_string` | (required) | PostgreSQL connection string |
| `write_mode` | `BLOCKED` | Allow write operations (`BLOCKED`/`ALLOWED`) |
| `default_schema` | `public` | Default schema for queries |
| `max_rows` | `100` | Maximum rows returned |
| `timeout_seconds` | `30` | Query timeout |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_URI` | PostgreSQL connection string |
| `POSTGRES_WRITE_MODE` | `blocked` or `allowed` |
| `POSTGRES_DEFAULT_SCHEMA` | Default schema |
| `POSTGRES_MAX_ROWS` | Max rows |
| `GOOGLE_API_KEY` | Gemini API key |
| `GEMINI_MODEL` | Model name (default: `gemini-2.0-flash`) |

## Tool Details

### list_schemas

```python
# Returns all schemas with table counts
{
    "status": "success",
    "schemas": [
        {"name": "public", "table_count": 4},
        {"name": "analytics", "table_count": 2}
    ]
}
```

### list_tables

```python
# Returns tables with row counts
{
    "status": "success",
    "schema": "public",
    "tables": [
        {"name": "customers", "row_count": 100, "description": ""},
        {"name": "orders", "row_count": 500, "description": ""}
    ]
}
```

### get_table_info

```python
# Returns columns, keys, and sample data
{
    "status": "success",
    "table": "customers",
    "schema": "public",
    "columns": [
        {"name": "id", "type": "integer", "nullable": false, "default": ""},
        {"name": "name", "type": "text", "nullable": true, "default": ""}
    ],
    "primary_key": ["id"],
    "foreign_keys": [],
    "sample_rows": [[1, "John"], [2, "Jane"]]
}
```

### execute_sql

```python
# Returns query results
{
    "status": "success",
    "query": "SELECT * FROM customers LIMIT 5",
    "columns": ["id", "name"],
    "rows": [[1, "John"], [2, "Jane"]],
    "row_count": 2
}
```

### ask_data_insights

```python
# Answers natural language questions
{
    "status": "success",
    "question": "How many customers do we have?",
    "sql_query": "SELECT COUNT(*) FROM customers",
    "answer": "You have 100 customers in the database.",
    "columns": ["count"],
    "data": [[100]],
    "row_count": 1
}
```

## Comparison with POCs

| Aspect | POC-2 (MCP Toolbox) | PostgresToolset |
|--------|---------------------|-----------------|
| Tools | 12+ predefined | 5 focused |
| SQL | Predefined templates | Dynamic + insights |
| Token usage | Higher (verbose) | Lower (concise) |
| Flexibility | Limited to templates | Full SQL + NL |
| ADK native | Yes | Yes |

## License

MIT
