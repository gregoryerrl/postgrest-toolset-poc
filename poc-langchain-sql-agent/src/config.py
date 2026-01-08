"""Configuration management."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_config():
    """Get configuration from environment variables."""
    config = {
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "postgres_uri": os.getenv("POSTGRES_URI"),
    }

    # Validate required config
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    return config
