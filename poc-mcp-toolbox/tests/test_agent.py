"""Tests for MCP Toolbox agent."""

import pytest
from agent.agent import create_agent, query


class TestToolboxAgent:
    """Test cases for MCP Toolbox agent."""

    def test_agent_creates_with_all_tools(self):
        """Test agent creation with all tools."""
        agent = create_agent("all-tools")
        assert agent is not None

    def test_agent_creates_with_schema_tools(self):
        """Test agent creation with schema tools only."""
        agent = create_agent("schema-tools")
        assert agent is not None

    def test_list_tables_query(self):
        """Test listing tables."""
        result = query("What tables are in the database?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_customer_query(self):
        """Test customer-related query."""
        result = query("Show me all customers")
        assert isinstance(result, str)

    def test_order_query(self):
        """Test order-related query."""
        result = query("What orders are pending?")
        assert isinstance(result, str)

    def test_analytics_query(self):
        """Test analytics query."""
        result = query("What's the total revenue by order status?")
        assert isinstance(result, str)
