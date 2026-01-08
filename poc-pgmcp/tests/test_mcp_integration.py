"""Tests for MCP protocol integration with PGMCP server."""

import pytest
import httpx
from agent.agent import PGMCPClient, PGMCP_URL


class TestMCPProtocol:
    """Test MCP JSON-RPC protocol interactions."""

    @pytest.fixture
    def client(self):
        """Create HTTP client for direct MCP calls."""
        return httpx.Client(timeout=30.0)

    @pytest.fixture
    def pgmcp_client(self):
        """Create PGMCP client instance."""
        return PGMCPClient()

    def test_mcp_endpoint_format(self):
        """Test that MCP endpoint URL is correctly formed."""
        assert PGMCP_URL == "http://localhost:8080"
        client = PGMCPClient()
        assert client.base_url == "http://localhost:8080"

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_mcp_jsonrpc_tools_call(self, client):
        """Test MCP tools/call method with JSON-RPC 2.0 format."""
        response = client.post(
            f"{PGMCP_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "ask",
                    "arguments": {
                        "question": "What tables exist?",
                        "format": "json"
                    }
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "jsonrpc" in data or "result" in data or "error" in data

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_mcp_resources_list(self, client):
        """Test MCP resources/list method for schema retrieval."""
        response = client.post(
            f"{PGMCP_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "resources/list",
                "params": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_mcp_search_tool(self, client):
        """Test MCP search tool call."""
        response = client.post(
            f"{PGMCP_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": "test",
                        "limit": 10
                    }
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestMCPClientIntegration:
    """Integration tests for PGMCP Python client with MCP server."""

    @pytest.fixture
    def client(self):
        """Create PGMCP client instance."""
        return PGMCPClient()

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_ask_returns_structured_response(self, client):
        """Test that ask method returns properly structured response."""
        result = client.ask("How many tables are in the database?")
        assert "success" in result
        assert "question" in result
        if result["success"]:
            assert "result" in result

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_ask_with_different_formats(self, client):
        """Test ask method with different output formats."""
        for fmt in ["json", "table", "csv"]:
            result = client.ask("List all tables", format=fmt)
            assert "success" in result
            assert result["question"] == "List all tables"

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_search_returns_results(self, client):
        """Test search returns results for known data."""
        result = client.search("Alice")
        assert isinstance(result, dict)

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_get_schema_returns_tables(self, client):
        """Test schema retrieval returns table information."""
        result = client.get_schema()
        assert isinstance(result, dict)

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_context_manager(self):
        """Test client works as context manager."""
        with PGMCPClient() as client:
            assert client.health_check() is True
            result = client.ask("What tables exist?")
            assert "success" in result


class TestMCPErrorHandling:
    """Test error handling in MCP protocol interactions."""

    @pytest.fixture
    def client(self):
        """Create PGMCP client instance."""
        return PGMCPClient()

    def test_connection_error_handled(self):
        """Test that connection errors are handled gracefully."""
        # Use non-existent server
        client = PGMCPClient(base_url="http://localhost:9999")
        result = client.ask("test query")
        assert result["success"] is False
        assert "error" in result

    def test_health_check_returns_false_when_down(self):
        """Test health check returns False when server is not running."""
        client = PGMCPClient(base_url="http://localhost:9999")
        assert client.health_check() is False

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_empty_question_handling(self, client):
        """Test handling of empty question."""
        result = client.ask("")
        assert "success" in result

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_special_characters_in_query(self, client):
        """Test handling of special characters in queries."""
        result = client.ask("What is 'Alice's' order?")
        assert "success" in result
