"""PostgresToolset - ADK toolset for PostgreSQL databases.

Mirrors BigQueryToolset architecture with 5 focused tools:
1. list_schemas - List available schemas (like list_dataset_ids)
2. list_tables - List tables in a schema (like list_table_ids)
3. get_table_info - Get table metadata (same)
4. execute_sql - Run SQL queries (same)
5. ask_data_insights - Natural language to SQL (same)
"""

from typing import Optional
import psycopg

from google.adk.tools import FunctionTool
from google.adk.tools.base_toolset import BaseToolset
from google.genai import Client

from .config import PostgresConfig, LLMConfig, WriteMode


class PostgresToolset(BaseToolset):
    """ADK Toolset for PostgreSQL databases.

    Provides schema exploration, SQL execution, and natural language
    query capabilities mirroring BigQueryToolset.

    Example:
        config = PostgresConfig.from_env()
        toolset = PostgresToolset(config)
        agent = Agent(tools=[toolset])
    """

    def __init__(
        self,
        postgres_config: PostgresConfig,
        llm_config: Optional[LLMConfig] = None,
    ):
        """Initialize PostgresToolset.

        Args:
            postgres_config: PostgreSQL connection and behavior config
            llm_config: LLM config for ask_data_insights (uses defaults if not provided)
        """
        self._pg_config = postgres_config
        self._llm_config = llm_config or LLMConfig.from_env()
        self._conn: Optional[psycopg.Connection] = None
        self._genai_client: Optional[Client] = None

        # Create tools
        self._tools = [
            FunctionTool(func=self._list_schemas),
            FunctionTool(func=self._list_tables),
            FunctionTool(func=self._get_table_info),
            FunctionTool(func=self._execute_sql),
            FunctionTool(func=self._ask_data_insights),
        ]

    def _get_connection(self) -> psycopg.Connection:
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(
                self._pg_config.connection_string,
                autocommit=True,
            )
        return self._conn

    def _get_genai_client(self) -> Client:
        """Get or create GenAI client."""
        if self._genai_client is None:
            self._genai_client = Client(api_key=self._llm_config.api_key)
        return self._genai_client

    async def get_tools(self, readonly_context=None) -> list:
        """Return available tools.

        Part of BaseToolset interface - called by ADK agent.
        """
        return self._tools

    async def close(self) -> None:
        """Clean up resources.

        Part of BaseToolset interface - called when toolset is no longer needed.
        """
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    # =========================================================================
    # Tool 1: list_schemas
    # =========================================================================
    def _list_schemas(self) -> dict:
        """List all schemas in the PostgreSQL database.

        Use this tool to discover available schemas before exploring tables.
        Returns schema names and their table counts.

        Returns:
            dict: {
                "status": "success" or "error",
                "schemas": [{"name": str, "table_count": int}, ...],
                "error_message": str (only if status is "error")
            }
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        n.nspname as schema_name,
                        COUNT(c.relname) as table_count
                    FROM pg_namespace n
                    LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind = 'r'
                    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    GROUP BY n.nspname
                    ORDER BY n.nspname
                """)
                rows = cur.fetchall()

            return {
                "status": "success",
                "schemas": [
                    {"name": row[0], "table_count": row[1]}
                    for row in rows
                ]
            }
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    # =========================================================================
    # Tool 2: list_tables
    # =========================================================================
    def _list_tables(self, schema_name: str) -> dict:
        """List all tables in a PostgreSQL schema.

        Use this tool after list_schemas to discover tables.
        Returns table names with row counts and descriptions.

        Args:
            schema_name: The schema to list tables from (e.g., "public")

        Returns:
            dict: {
                "status": "success" or "error",
                "schema": str,
                "tables": [{"name": str, "row_count": int, "description": str}, ...],
                "error_message": str (only if status is "error")
            }
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        t.tablename,
                        COALESCE(s.n_live_tup, 0) as row_count,
                        COALESCE(d.description, '') as description
                    FROM pg_tables t
                    LEFT JOIN pg_stat_user_tables s
                        ON t.tablename = s.relname AND t.schemaname = s.schemaname
                    LEFT JOIN pg_class c
                        ON c.relname = t.tablename
                    LEFT JOIN pg_namespace n
                        ON n.oid = c.relnamespace AND n.nspname = t.schemaname
                    LEFT JOIN pg_description d
                        ON d.objoid = c.oid AND d.objsubid = 0
                    WHERE t.schemaname = %s
                    ORDER BY t.tablename
                """, (schema_name,))
                rows = cur.fetchall()

            return {
                "status": "success",
                "schema": schema_name,
                "tables": [
                    {"name": row[0], "row_count": row[1], "description": row[2]}
                    for row in rows
                ]
            }
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    # =========================================================================
    # Tool 3: get_table_info
    # =========================================================================
    def _get_table_info(self, table_name: str, schema_name: str = "public") -> dict:
        """Get detailed metadata about a PostgreSQL table.

        Use this tool to understand table structure before querying.
        Returns columns, types, constraints, and sample data.

        Args:
            table_name: The table to describe
            schema_name: The schema containing the table (default: "public")

        Returns:
            dict: {
                "status": "success" or "error",
                "table": str,
                "schema": str,
                "columns": [{"name": str, "type": str, "nullable": bool, "default": str}, ...],
                "primary_key": [str, ...],
                "foreign_keys": [{"column": str, "references": str}, ...],
                "sample_rows": [[value, ...], ...] (first 3 rows),
                "error_message": str (only if status is "error")
            }
        """
        try:
            conn = self._get_connection()
            result = {
                "status": "success",
                "table": table_name,
                "schema": schema_name,
            }

            with conn.cursor() as cur:
                # Get columns
                cur.execute("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable = 'YES' as nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, table_name))
                columns = cur.fetchall()

                result["columns"] = [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2],
                        "default": col[3] or ""
                    }
                    for col in columns
                ]

                # Get primary key
                cur.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    JOIN pg_class c ON c.oid = i.indrelid
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE i.indisprimary AND c.relname = %s AND n.nspname = %s
                """, (table_name, schema_name))
                pk_rows = cur.fetchall()
                result["primary_key"] = [row[0] for row in pk_rows]

                # Get foreign keys
                cur.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_schema || '.' || ccu.table_name || '.' || ccu.column_name as references
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = %s AND tc.table_name = %s
                """, (schema_name, table_name))
                fk_rows = cur.fetchall()
                result["foreign_keys"] = [
                    {"column": row[0], "references": row[1]}
                    for row in fk_rows
                ]

                # Get sample rows (first 3)
                cur.execute(
                    f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT 3'
                )
                sample_rows = cur.fetchall()
                result["sample_rows"] = [list(row) for row in sample_rows]

            return result
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    # =========================================================================
    # Tool 4: execute_sql
    # =========================================================================
    def _execute_sql(self, sql_query: str) -> dict:
        """Execute a SQL query on the PostgreSQL database.

        Use this tool to run SQL queries. Returns results as rows.
        Write operations are blocked by default for safety.

        Args:
            sql_query: The SQL query to execute

        Returns:
            dict: {
                "status": "success" or "error",
                "query": str,
                "columns": [str, ...],
                "rows": [[value, ...], ...],
                "row_count": int,
                "error_message": str (only if status is "error")
            }
        """
        try:
            # Check write mode
            query_upper = sql_query.strip().upper()
            is_write = any(query_upper.startswith(kw) for kw in
                          ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"])

            if is_write and self._pg_config.write_mode == WriteMode.BLOCKED:
                return {
                    "status": "error",
                    "error_message": "Write operations are blocked. Only SELECT queries allowed."
                }

            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(sql_query)

                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchmany(self._pg_config.max_rows)
                    return {
                        "status": "success",
                        "query": sql_query,
                        "columns": columns,
                        "rows": [list(row) for row in rows],
                        "row_count": len(rows),
                    }
                else:
                    return {
                        "status": "success",
                        "query": sql_query,
                        "message": f"Query executed successfully. Rows affected: {cur.rowcount}",
                    }
        except Exception as e:
            return {"status": "error", "query": sql_query, "error_message": str(e)}

    # =========================================================================
    # Tool 5: ask_data_insights
    # =========================================================================
    def _ask_data_insights(self, question: str, schema_name: str = "public") -> dict:
        """Answer questions about data using natural language.

        Use this tool when users ask questions about data in plain English.
        Converts the question to SQL, executes it, and provides insights.

        Args:
            question: Natural language question about the data
            schema_name: The schema to query (default: "public")

        Returns:
            dict: {
                "status": "success" or "error",
                "question": str,
                "sql_query": str,
                "answer": str,
                "data": [[value, ...], ...],
                "error_message": str (only if status is "error")
            }
        """
        try:
            # Get schema context
            tables_result = self._list_tables(schema_name)
            if tables_result["status"] == "error":
                return tables_result

            # Get detailed info for each table
            schema_context = []
            for table in tables_result["tables"][:10]:  # Limit to 10 tables
                table_info = self._get_table_info(table["name"], schema_name)
                if table_info["status"] == "success":
                    cols = ", ".join([
                        f"{c['name']} ({c['type']})"
                        for c in table_info["columns"]
                    ])
                    schema_context.append(f"- {table['name']}: {cols}")

            schema_str = "\n".join(schema_context)

            # Generate SQL using LLM
            client = self._get_genai_client()
            prompt = f"""You are a SQL expert. Given the following PostgreSQL schema and a question, generate a SQL query.

Schema ({schema_name}):
{schema_str}

Question: {question}

Rules:
1. Return ONLY the SQL query, no explanations
2. Use only SELECT statements
3. Limit results to {self._pg_config.max_rows} rows
4. Use proper table qualification with schema name when needed

SQL:"""

            response = client.models.generate_content(
                model=self._llm_config.model,
                contents=prompt,
            )

            sql_query = response.text.strip()
            # Clean up markdown if present
            if sql_query.startswith("```"):
                sql_query = sql_query.split("\n", 1)[1]
            if sql_query.endswith("```"):
                sql_query = sql_query.rsplit("```", 1)[0]
            sql_query = sql_query.strip()

            # Execute the query
            exec_result = self._execute_sql(sql_query)
            if exec_result["status"] == "error":
                return {
                    "status": "error",
                    "question": question,
                    "sql_query": sql_query,
                    "error_message": exec_result["error_message"],
                }

            # Generate natural language answer
            data_preview = str(exec_result.get("rows", [])[:5])
            answer_prompt = f"""Based on this SQL query result, provide a concise answer.

Question: {question}
SQL: {sql_query}
Data (preview): {data_preview}
Row count: {exec_result.get('row_count', 0)}

Answer (1-2 sentences):"""

            answer_response = client.models.generate_content(
                model=self._llm_config.model,
                contents=answer_prompt,
            )

            return {
                "status": "success",
                "question": question,
                "sql_query": sql_query,
                "answer": answer_response.text.strip(),
                "columns": exec_result.get("columns", []),
                "data": exec_result.get("rows", []),
                "row_count": exec_result.get("row_count", 0),
            }

        except Exception as e:
            return {
                "status": "error",
                "question": question,
                "error_message": str(e),
            }
