"""Tests for PGMCP Python client."""

import pytest
from agent.agent import PGMCPClient, query


class TestPGMCPClient:
    """Test cases for PGMCP client."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        return PGMCPClient()

    def test_client_initializes(self, client):
        """Test client initialization."""
        assert client is not None
        assert client.base_url == "http://localhost:8080"

    def test_health_check(self, client):
        """Test server health check."""
        # This will fail if server isn't running, which is expected
        result = client.health_check()
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_ask_simple_question(self, client):
        """Test asking a simple question."""
        result = client.ask("What tables are in the database?")
        assert "success" in result

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_ask_count_query(self, client):
        """Test a count query."""
        result = client.ask("How many customers are there?")
        assert "success" in result

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_search(self, client):
        """Test free-text search."""
        result = client.search("Alice")
        assert isinstance(result, dict)

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_get_schema(self, client):
        """Test schema retrieval."""
        result = client.get_schema()
        assert isinstance(result, dict)


class TestQueryFunction:
    """Test the convenience query function."""

    @pytest.mark.skipif(
        not PGMCPClient().health_check(),
        reason="PGMCP server not running"
    )
    def test_query_returns_string(self):
        """Test that query returns a string."""
        result = query("What tables exist?")
        assert isinstance(result, str)
