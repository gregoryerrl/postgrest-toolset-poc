"""Tests for PostgresToolset."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from src import PostgresToolset, PostgresConfig, WriteMode


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    return PostgresConfig(
        connection_string="postgresql://test:test@localhost:5432/testdb",
        write_mode=WriteMode.BLOCKED,
        max_rows=10,
    )


@pytest.fixture
def toolset(mock_config):
    """Create a toolset with mock config."""
    return PostgresToolset(mock_config)


class TestPostgresConfig:
    """Tests for PostgresConfig."""

    def test_default_values(self):
        """Test default config values."""
        config = PostgresConfig(connection_string="postgresql://test@localhost/db")
        assert config.write_mode == WriteMode.BLOCKED
        assert config.default_schema == "public"
        assert config.max_rows == 100
        assert config.timeout_seconds == 30

    def test_from_env(self):
        """Test creating config from environment."""
        with patch.dict(os.environ, {
            "POSTGRES_URI": "postgresql://user:pass@host:5432/db",
            "POSTGRES_WRITE_MODE": "allowed",
            "POSTGRES_DEFAULT_SCHEMA": "myschema",
            "POSTGRES_MAX_ROWS": "50",
        }):
            config = PostgresConfig.from_env()
            assert config.connection_string == "postgresql://user:pass@host:5432/db"
            assert config.write_mode == WriteMode.ALLOWED
            assert config.default_schema == "myschema"
            assert config.max_rows == 50

    def test_from_env_missing_uri(self):
        """Test error when URI is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing"):
                PostgresConfig.from_env()


class TestWriteMode:
    """Tests for WriteMode."""

    def test_blocked_mode(self, toolset):
        """Test that write queries are blocked by default."""
        result = toolset._execute_sql("INSERT INTO test VALUES (1)")
        assert result["status"] == "error"
        assert "blocked" in result["error_message"].lower()

    def test_blocked_detects_write_keywords(self, mock_config):
        """Test detection of write keywords."""
        mock_config.write_mode = WriteMode.BLOCKED
        toolset = PostgresToolset(mock_config)

        for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]:
            result = toolset._execute_sql(f"{keyword} something")
            assert result["status"] == "error"


class TestToolset:
    """Tests for PostgresToolset methods."""

    @pytest.mark.asyncio
    async def test_get_tools(self, toolset):
        """Test that get_tools returns the 5 tools."""
        tools = await toolset.get_tools()
        assert len(tools) == 5

        tool_names = {t.func.__name__ for t in tools}
        expected = {
            "_list_schemas",
            "_list_tables",
            "_get_table_info",
            "_execute_sql",
            "_ask_data_insights",
        }
        assert tool_names == expected

    @pytest.mark.asyncio
    async def test_close(self, toolset):
        """Test that close cleans up resources."""
        mock_conn = Mock()
        mock_conn.closed = False
        toolset._conn = mock_conn

        await toolset.close()

        mock_conn.close.assert_called_once()
        assert toolset._conn is None


class TestListSchemas:
    """Tests for list_schemas tool."""

    def test_returns_dict_with_status(self, toolset):
        """Test return format includes status."""
        with patch.object(toolset, "_get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [("public", 4)]
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = toolset._list_schemas()

            assert "status" in result
            assert result["status"] == "success"
            assert "schemas" in result

    def test_error_handling(self, toolset):
        """Test error handling."""
        with patch.object(toolset, "_get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Connection failed")

            result = toolset._list_schemas()

            assert result["status"] == "error"
            assert "error_message" in result


class TestListTables:
    """Tests for list_tables tool."""

    def test_returns_tables_for_schema(self, toolset):
        """Test listing tables in a schema."""
        with patch.object(toolset, "_get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("customers", 100, ""),
                ("orders", 50, ""),
            ]
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = toolset._list_tables("public")

            assert result["status"] == "success"
            assert result["schema"] == "public"
            assert len(result["tables"]) == 2


class TestGetTableInfo:
    """Tests for get_table_info tool."""

    def test_returns_column_info(self, toolset):
        """Test getting table metadata."""
        with patch.object(toolset, "_get_connection") as mock_conn:
            mock_cursor = MagicMock()
            # Columns query
            mock_cursor.fetchall.side_effect = [
                [("id", "integer", False, "")],  # columns
                [("id",)],  # primary key
                [],  # foreign keys
                [[1, "test"]],  # sample rows
            ]
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = toolset._get_table_info("customers")

            assert result["status"] == "success"
            assert "columns" in result
            assert "primary_key" in result


class TestExecuteSql:
    """Tests for execute_sql tool."""

    def test_executes_select(self, toolset):
        """Test executing SELECT query."""
        with patch.object(toolset, "_get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",), ("name",)]
            mock_cursor.fetchmany.return_value = [[1, "test"]]
            mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            result = toolset._execute_sql("SELECT * FROM test")

            assert result["status"] == "success"
            assert "columns" in result
            assert "rows" in result


class TestAskDataInsights:
    """Tests for ask_data_insights tool."""

    def test_generates_sql_and_answers(self, toolset):
        """Test natural language to SQL."""
        with patch.object(toolset, "_list_tables") as mock_list:
            mock_list.return_value = {
                "status": "success",
                "tables": [{"name": "customers", "row_count": 100, "description": ""}],
            }

            with patch.object(toolset, "_get_table_info") as mock_info:
                mock_info.return_value = {
                    "status": "success",
                    "columns": [{"name": "id", "type": "integer"}],
                }

                with patch.object(toolset, "_execute_sql") as mock_exec:
                    mock_exec.return_value = {
                        "status": "success",
                        "columns": ["count"],
                        "rows": [[100]],
                        "row_count": 1,
                    }

                    with patch.object(toolset, "_get_genai_client") as mock_client:
                        mock_response = Mock()
                        mock_response.text = "SELECT COUNT(*) FROM customers"
                        mock_client.return_value.models.generate_content.return_value = mock_response

                        result = toolset._ask_data_insights("How many customers?")

                        assert "status" in result
