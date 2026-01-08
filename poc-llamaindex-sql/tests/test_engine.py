"""Tests for LlamaIndex SQL query engine."""

import pytest
from src.engine import (
    create_sql_database,
    create_query_engine,
    create_retriever_query_engine,
    query
)
from src.chat import create_chat_engine, chat


class TestSQLDatabase:
    """Test SQL database creation."""

    def test_creates_database(self):
        """Test that SQL database is created."""
        db = create_sql_database()
        assert db is not None

    def test_has_tables(self):
        """Test that tables are discovered."""
        db = create_sql_database()
        tables = list(db.get_usable_table_names())
        assert len(tables) > 0

    def test_can_get_table_info(self):
        """Test getting table information."""
        db = create_sql_database()
        tables = list(db.get_usable_table_names())
        if tables:
            info = db.get_single_table_info(tables[0])
            assert len(info) > 0


class TestQueryEngine:
    """Test query engine functionality."""

    def test_creates_query_engine(self):
        """Test query engine creation."""
        engine = create_query_engine(verbose=False)
        assert engine is not None

    def test_simple_query(self):
        """Test a simple query."""
        result = query("How many tables are in the database?", verbose=False)
        assert "answer" in result
        assert len(result["answer"]) > 0

    def test_count_query(self):
        """Test a count query."""
        result = query("How many customers are there?", verbose=False)
        assert "answer" in result

    def test_returns_sql(self):
        """Test that SQL is returned in metadata."""
        result = query("Count all orders", verbose=False)
        assert "sql" in result


class TestRetrieverEngine:
    """Test retriever-based query engine."""

    def test_creates_retriever_engine(self):
        """Test retriever engine creation."""
        engine = create_retriever_query_engine(verbose=False)
        assert engine is not None

    def test_query_with_retriever(self):
        """Test query using retriever."""
        result = query(
            "What's the total order value?",
            use_retriever=True,
            verbose=False
        )
        assert "answer" in result


class TestChatEngine:
    """Test chat engine with memory."""

    def test_creates_chat_engine(self):
        """Test chat engine creation."""
        engine = create_chat_engine()
        assert engine is not None

    def test_chat_response(self):
        """Test chat returns response."""
        response = chat("What tables exist?")
        assert isinstance(response, str)
        assert len(response) > 0
