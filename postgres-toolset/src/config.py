"""Configuration for PostgresToolset.

Mirrors BigQueryToolConfig patterns for consistency.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import os


class WriteMode(Enum):
    """Controls whether write operations are allowed.

    BLOCKED: Only SELECT queries allowed (recommended for safety)
    ALLOWED: INSERT, UPDATE, DELETE queries allowed
    """
    BLOCKED = "blocked"
    ALLOWED = "allowed"


@dataclass
class PostgresConfig:
    """Configuration for PostgreSQL connection and toolset behavior.

    Args:
        connection_string: PostgreSQL connection string (postgres://user:pass@host:port/db)
        write_mode: Whether to allow write operations (default: BLOCKED)
        default_schema: Default schema to use (default: "public")
        max_rows: Maximum rows to return from queries (default: 100)
        timeout_seconds: Query timeout in seconds (default: 30)
    """
    connection_string: str
    write_mode: WriteMode = WriteMode.BLOCKED
    default_schema: str = "public"
    max_rows: int = 100
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls, prefix: str = "POSTGRES") -> "PostgresConfig":
        """Create config from environment variables.

        Looks for:
        - {prefix}_URI or {prefix}_CONNECTION_STRING
        - {prefix}_WRITE_MODE (blocked/allowed)
        - {prefix}_DEFAULT_SCHEMA
        - {prefix}_MAX_ROWS
        - {prefix}_TIMEOUT
        """
        conn_str = os.getenv(f"{prefix}_URI") or os.getenv(f"{prefix}_CONNECTION_STRING")
        if not conn_str:
            raise ValueError(f"Missing {prefix}_URI or {prefix}_CONNECTION_STRING environment variable")

        write_mode_str = os.getenv(f"{prefix}_WRITE_MODE", "blocked").lower()
        write_mode = WriteMode.ALLOWED if write_mode_str == "allowed" else WriteMode.BLOCKED

        return cls(
            connection_string=conn_str,
            write_mode=write_mode,
            default_schema=os.getenv(f"{prefix}_DEFAULT_SCHEMA", "public"),
            max_rows=int(os.getenv(f"{prefix}_MAX_ROWS", "100")),
            timeout_seconds=int(os.getenv(f"{prefix}_TIMEOUT", "30")),
        )


@dataclass
class LLMConfig:
    """Configuration for the LLM used in ask_data_insights.

    Args:
        model: Model name (default: gemini-2.0-flash)
        api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
        temperature: Sampling temperature (default: 0 for deterministic SQL)
    """
    model: str = "gemini-2.0-flash"
    api_key: Optional[str] = None
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables."""
        return cls(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0")),
        )
