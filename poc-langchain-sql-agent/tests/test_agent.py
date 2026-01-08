"""Tests for the LangChain SQL agent."""

import pytest
from src.agent import create_postgres_agent, query


class TestSQLAgent:
    """Test cases for SQL agent functionality."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return create_postgres_agent(verbose=False)

    def test_agent_creates_successfully(self, agent):
        """Test that agent initializes without error."""
        assert agent is not None

    def test_list_tables(self, agent):
        """Test that agent can list tables."""
        result = agent.invoke({"input": "What tables are in the database?"})
        assert "output" in result
        assert len(result["output"]) > 0

    def test_simple_count_query(self, agent):
        """Test a simple count query."""
        result = agent.invoke({"input": "How many tables are in the database?"})
        assert "output" in result

    def test_schema_description(self, agent):
        """Test getting schema information."""
        result = agent.invoke({"input": "Describe the schema of the database"})
        assert "output" in result

    def test_query_function(self):
        """Test the convenience query function."""
        result = query("What tables exist?", verbose=False)
        assert isinstance(result, str)
        assert len(result) > 0


class TestErrorHandling:
    """Test error handling capabilities."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return create_postgres_agent(verbose=False)

    def test_handles_nonexistent_table(self, agent):
        """Test that agent handles queries about nonexistent tables."""
        result = agent.invoke({
            "input": "How many rows are in the xyz_nonexistent_table_123?"
        })
        # Should not crash, should provide helpful response
        assert "output" in result

    def test_handles_ambiguous_query(self, agent):
        """Test that agent handles ambiguous queries."""
        result = agent.invoke({"input": "Show me everything"})
        assert "output" in result
