# PostgreSQL Natural Language Query POCs

A comparative study of 4 different approaches for querying PostgreSQL databases using natural language. Each POC implements a text-to-SQL solution with different tradeoffs.

## Quick Comparison

| POC | Tool | LLM | SQL Generation | Best For |
|-----|------|-----|----------------|----------|
| 1 | LangChain SQL Agent | Gemini | Dynamic (auto-generated) | Quick prototyping, flexible queries |
| 2 | Google MCP Toolbox | Gemini | Predefined (tools.yaml) | Production apps, controlled access |
| 3 | PGMCP | OpenAI | Dynamic (NL-to-SQL) | MCP-native integrations (Claude, Cursor) |
| 4 | LlamaIndex | Gemini | Schema-aware (indexed) | Complex schemas, conversational |

## Understanding the Approaches

### Dynamic SQL vs Predefined Queries

**Dynamic SQL Generation** (POCs 1, 3, 4)
- LLM generates SQL on-the-fly based on natural language
- More flexible - can handle any question
- Higher risk - potential for SQL injection or unintended queries
- Better for exploration and ad-hoc analysis

**Predefined Queries** (POC 2)
- SQL templates defined in configuration (tools.yaml)
- LLM selects which predefined query to use
- Safer - only allowed queries can execute
- Better for production apps with known query patterns

### Architecture Patterns

```
┌─────────────────────────────────────────────────────────────────────┐
│                     POC 1: LangChain SQL Agent                       │
│  ┌────────┐    ┌─────────────┐    ┌────────────┐    ┌──────────┐   │
│  │ User   │───▶│   Gemini    │───▶│ SQL Agent  │───▶│ Postgres │   │
│  │ Query  │    │   (LLM)     │    │ (Generate) │    │   DB     │   │
│  └────────┘    └─────────────┘    └────────────┘    └──────────┘   │
│                                                                      │
│  Flow: User → LLM generates SQL → Execute → LLM interprets result   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    POC 2: Google MCP Toolbox                         │
│  ┌────────┐    ┌─────────────┐    ┌────────────┐    ┌──────────┐   │
│  │ User   │───▶│   Gemini    │───▶│  Toolbox   │───▶│ Postgres │   │
│  │ Query  │    │   (LLM)     │    │ (Select)   │    │   DB     │   │
│  └────────┘    └─────────────┘    └────────────┘    └──────────┘   │
│                                          │                           │
│                                   ┌──────┴──────┐                    │
│                                   │ tools.yaml  │                    │
│                                   │ (predefined)│                    │
│                                   └─────────────┘                    │
│  Flow: User → LLM selects tool → Toolbox runs predefined SQL        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      POC 3: PGMCP Server                             │
│  ┌────────┐    ┌─────────────┐    ┌────────────┐    ┌──────────┐   │
│  │ Client │───▶│   PGMCP     │───▶│  OpenAI    │───▶│ Postgres │   │
│  │ (MCP)  │    │  Server     │    │   (LLM)    │    │   DB     │   │
│  └────────┘    └─────────────┘    └────────────┘    └──────────┘   │
│                                                                      │
│  Flow: MCP Client → PGMCP → OpenAI generates SQL → Execute          │
│  Note: Works with Claude Desktop, Cursor, VS Code via MCP protocol  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    POC 4: LlamaIndex Engine                          │
│  ┌────────┐    ┌─────────────┐    ┌────────────┐    ┌──────────┐   │
│  │ User   │───▶│Schema Index │───▶│  Gemini    │───▶│ Postgres │   │
│  │ Query  │    │(Embeddings) │    │   (LLM)    │    │   DB     │   │
│  └────────┘    └─────────────┘    └────────────┘    └──────────┘   │
│                                                                      │
│  Flow: User → Find relevant tables → Generate SQL → Execute         │
│  Note: Schema-aware indexing improves SQL accuracy                  │
└─────────────────────────────────────────────────────────────────────┘
```

## POC Details

### POC 1: LangChain SQL Agent

**What it is:** LangChain's `create_sql_agent` - a mature, battle-tested text-to-SQL solution.

**Key Features:**
- Built-in error recovery (retries failed queries automatically)
- Schema exploration tools
- Sample row context for better SQL understanding
- Works with any SQLAlchemy database

**When to use:**
- Quick prototyping and exploration
- When you need flexible, ad-hoc queries
- When error recovery is important

**Code pattern:**
```python
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
agent = create_sql_agent(llm=llm, db=db, verbose=True)
result = agent.invoke({"input": "How many customers do we have?"})
```

---

### POC 2: Google MCP Toolbox

**What it is:** Google's official database tooling that uses predefined SQL queries.

**Key Features:**
- Predefined queries in `tools.yaml` - you control exactly what SQL runs
- Better security - no arbitrary SQL generation
- Native ADK (Agent Development Kit) integration
- Audit trail of which tools were used

**When to use:**
- Production applications
- When security is critical
- When you have known query patterns
- When integrating with Google's ADK

**Code pattern:**
```yaml
# tools.yaml
tools:
  get-customer-count:
    kind: postgres-sql
    source: postgres-source
    description: "Get total number of customers"
    statement: "SELECT COUNT(*) as total FROM customers"
```

```python
from google import adk
from toolbox.core import ToolboxClient

client = ToolboxClient("http://localhost:5000")
tools = client.load_toolset("postgres-tools")
agent = adk.Agent(tools=tools)
```

---

### POC 3: PGMCP

**What it is:** An open-source MCP server built specifically for PostgreSQL natural language queries.

**Key Features:**
- MCP protocol native - works with Claude Desktop, Cursor, VS Code
- Auto-pagination for large results
- Streaming support
- Read-only enforcement for safety
- Full-text search across all columns

**When to use:**
- When integrating with MCP-compatible clients
- When you need streaming for large datasets
- When read-only safety is important

**Requires:** Go 1.21+, OpenAI API key (not Gemini)

**Integration:**
```json
// Claude Desktop config
{
  "mcpServers": {
    "pgmcp": {
      "command": "./pgmcp",
      "args": ["--database-url", "postgres://..."]
    }
  }
}
```

---

### POC 4: LlamaIndex NLSQLQueryEngine

**What it is:** LlamaIndex's schema-aware SQL engine with table retrieval.

**Key Features:**
- Schema indexing - embeds table structures for better SQL
- Table retrieval - identifies relevant tables before querying
- Conversation memory in chat mode
- Sample rows improve understanding
- Multiple query modes (direct, retriever, chat)

**When to use:**
- Complex databases with many tables
- When SQL accuracy is critical
- When you need conversational follow-ups
- When working with unfamiliar schemas

**Code pattern:**
```python
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine

sql_database = SQLDatabase(engine, include_tables=["customers", "orders"])
query_engine = NLSQLTableQueryEngine(sql_database=sql_database, llm=llm)
response = query_engine.query("Who are the top customers?")
```

---

## Decision Guide

```
                    ┌─────────────────────────┐
                    │ Do you need MCP         │
                    │ integration (Claude,    │
                    │ Cursor, VS Code)?       │
                    └───────────┬─────────────┘
                          │
            ┌─────────────┴─────────────┐
            │ YES                       │ NO
            ▼                           ▼
    ┌───────────────┐           ┌─────────────────────┐
    │   POC 3:      │           │ Do you need         │
    │   PGMCP       │           │ predefined, safe    │
    │               │           │ queries?            │
    └───────────────┘           └──────────┬──────────┘
                                     │
                       ┌─────────────┴─────────────┐
                       │ YES                       │ NO
                       ▼                           ▼
               ┌───────────────┐           ┌─────────────────────┐
               │   POC 2:      │           │ Is the database     │
               │   MCP Toolbox │           │ schema complex      │
               │               │           │ (many tables)?      │
               └───────────────┘           └──────────┬──────────┘
                                                 │
                                   ┌─────────────┴─────────────┐
                                   │ YES                       │ NO
                                   ▼                           ▼
                           ┌───────────────┐           ┌───────────────┐
                           │   POC 4:      │           │   POC 1:      │
                           │   LlamaIndex  │           │   LangChain   │
                           │               │           │               │
                           └───────────────┘           └───────────────┘
```

## Shared Setup

All POCs use the same sample PostgreSQL database:

```bash
# Start PostgreSQL with Docker
docker run -d --name postgres-poc \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:16

# Setup sample data (same for all POCs)
psql -h localhost -U postgres -d testdb -f shared/setup_sample_db.sql
```

### Sample Database Schema

```
customers ──────────────────┐
├── id (PK)                 │
├── name                    │
├── email                   │
├── city                    │
└── country                 │
                            │
products ───────────────────┤
├── id (PK)                 │
├── name                    │
├── category                │
├── price                   │
└── stock_quantity          │
                            │
orders ─────────────────────┤
├── id (PK)                 │
├── customer_id (FK) ───────┘
├── order_date
├── status
└── total_amount

order_items ────────────────
├── id (PK)
├── order_id (FK) ──────────► orders
├── product_id (FK) ────────► products
├── quantity
└── unit_price
```

## Test Queries

Try these queries with each POC to compare results:

**Basic:**
- "What tables are in the database?"
- "How many customers do we have?"

**Aggregation:**
- "What's the total revenue from completed orders?"
- "What's the average order value?"

**Joins:**
- "Who are the top 3 customers by order value?"
- "Show pending orders with customer names"

**Complex:**
- "Which products have never been ordered?"
- "What's the month-over-month revenue trend?"

## Running Each POC

```bash
# POC 1: LangChain
cd poc-langchain-sql-agent
pip install -r requirements.txt
python -m src.agent

# POC 2: MCP Toolbox
cd poc-mcp-toolbox
./scripts/install_toolbox.sh
./scripts/run_toolbox.sh &
python -m agent.agent

# POC 3: PGMCP
cd poc-pgmcp
./scripts/install_pgmcp.sh
./pgmcp --database-url "postgres://..."

# POC 4: LlamaIndex
cd poc-llamaindex-sql
pip install -r requirements.txt
python -m src.engine
```

## Environment Variables

Create a `.env` file in each POC directory:

```bash
# Common
POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/testdb

# For POCs 1, 2, 4 (Gemini)
GOOGLE_API_KEY=your-gemini-api-key

# For POC 3 (OpenAI)
OPENAI_API_KEY=your-openai-api-key
```

## Further Learning

- [LangChain SQL Agent Docs](https://python.langchain.com/docs/tutorials/sql_qa/)
- [Google MCP Toolbox](https://github.com/googleapis/genai-toolbox)
- [PGMCP GitHub](https://github.com/stuzero/pg-mcp-server)
- [LlamaIndex SQL Guide](https://docs.llamaindex.ai/en/stable/examples/index_structs/struct_indices/SQLIndexDemo/)

## License

MIT
