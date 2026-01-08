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

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    return config


def setup_gemini():
    """Configure Gemini as the LLM for LlamaIndex."""
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.gemini import GeminiEmbedding
    from llama_index.core import Settings

    config = get_config()

    # Set up Gemini LLM
    Settings.llm = Gemini(
        api_key=config["google_api_key"],
        model="models/gemini-2.0-flash",
        temperature=0.1,
    )

    # Set up Gemini embeddings (for schema indexing)
    Settings.embed_model = GeminiEmbedding(
        api_key=config["google_api_key"],
        model_name="models/text-embedding-004",
    )

    return Settings.llm
