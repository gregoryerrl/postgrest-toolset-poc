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
