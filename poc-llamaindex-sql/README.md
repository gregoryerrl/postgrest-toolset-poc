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
+-------------------------------------------------------------+
|                    LlamaIndex                                |
+-------------------------------------------------------------+
|  +---------------+    +---------------+    +-------------+  |
|  | Schema Index  |--->| SQL Generator |--->|  Executor   |  |
|  |  (Embeddings) |    |   (Gemini)    |    | (SQLAlchemy)|  |
|  +---------------+    +---------------+    +-------------+  |
+-------------------------------------------------------------+
                              |
                              v
                    +-----------------+
                    |   PostgreSQL    |
                    +-----------------+
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
