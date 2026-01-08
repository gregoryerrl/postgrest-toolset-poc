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
