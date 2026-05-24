"""
UST Smart Chatbot — Embeddings Module
Manages the sentence-transformers embedding model for multilingual (Arabic + English) support.
Uses a singleton pattern to load the model once.
"""

import logging
from typing import List
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL

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
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            self._model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")

    def embed_text(self, text: str) -> List[float]:
        """Convert a single text to embedding vector."""
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors (batch)."""
        embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        return embeddings.tolist()

    def get_model_info(self) -> dict:
        """Return model metadata."""
        return {
            "model_name": EMBEDDING_MODEL,
            "max_seq_length": self._model.max_seq_length,
            "embedding_dimension": self._model.get_sentence_embedding_dimension(),
        }


# Global singleton instance
_embedding_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get or create the global EmbeddingManager instance."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager
