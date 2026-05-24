"""
UST Smart Chatbot — Vector Store Module
Manages ChromaDB for storing and retrieving document embeddings.
"""

import logging
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings

from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, TOP_K_RESULTS
from core.embeddings import get_embedding_manager

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages ChromaDB vector database operations."""

    def __init__(self):
        logger.info(f"Initializing ChromaDB at: {CHROMA_PERSIST_DIR}")
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self._embedder = get_embedding_manager()
        logger.info(f"ChromaDB initialized. Collection '{CHROMA_COLLECTION_NAME}' has {self._collection.count()} documents")

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> int:
        """Add documents to the vector store."""
        if not texts:
            return 0

        embeddings = self._embedder.embed_texts(texts)

        self._collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(f"Added {len(texts)} documents to vector store")
        return len(texts)

    def search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search for relevant documents.
        Returns list of {content, metadata, distance} sorted by relevance.
        """
        query_embedding = self._embedder.embed_text(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()) if self._collection.count() > 0 else top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - (distance / 2)
            similarity = 1 - (dist / 2)
            output.append({
                "content": doc,
                "metadata": meta,
                "similarity_score": round(similarity, 4),
            })

        return output

    def delete_documents(self, ids: List[str]) -> int:
        """Delete documents by their IDs."""
        if not ids:
            return 0
        self._collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from vector store")
        return len(ids)

    def delete_by_source(self, source: str) -> int:
        """Delete all documents from a specific source file."""
        # Get all documents with this source
        results = self._collection.get(
            where={"source": source},
            include=["metadatas"]
        )
        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks from source: {source}")
            return len(results["ids"])
        return 0

    def get_document_count(self) -> int:
        """Return total document count in the collection."""
        return self._collection.count()

    def reset(self):
        """Clear all documents from the collection."""
        self._client.delete_collection(CHROMA_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Vector store reset complete")

    def get_stats(self) -> dict:
        """Return vector store statistics."""
        return {
            "collection_name": CHROMA_COLLECTION_NAME,
            "total_chunks": self._collection.count(),
            "persist_directory": str(CHROMA_PERSIST_DIR),
        }


# Global singleton
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create the global VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
