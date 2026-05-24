"""
UST Smart Chatbot — Embeddings Module
Manages the Google Gemini embedding model for fast, zero-memory-cost search.
Uses a singleton pattern to load the model once.
"""

import logging
import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Singleton manager for the embedding model."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            logger.info("Loading Google Gemini embedding model")
            # We use text-embedding-004 which is extremely fast and free
            self._model = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=os.environ.get("GOOGLE_API_KEY")
            )
            logger.info("Embedding model loaded successfully")

    def embed_text(self, text: str) -> List[float]:
        """Convert a single text to embedding vector."""
        return self._model.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors (batch)."""
        return self._model.embed_documents(texts)

    def get_model_info(self) -> dict:
        """Return model metadata."""
        return {
            "model_name": "google/text-embedding-004",
            "embedding_dimension": 768, # Gemini embedding dimension
        }


# Global singleton instance
_embedding_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get or create the global EmbeddingManager instance."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager
