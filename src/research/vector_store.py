"""Vector store for embedding and searching financial documents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-backed vector store for financial documents.

    Collections:
    - earnings_reports: Quarterly earnings summaries
    - research_reports: AI-generated research
    - news: Financial news articles
    - journal: Decision journal entries
    """

    def __init__(self):
        settings = get_settings()
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_collection(self, name: str):
        return self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> int:
        """Add documents to a collection. Returns count added."""
        collection = self.get_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added {len(documents)} docs to '{collection_name}'")
        return len(documents)

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> dict:
        """Semantic search across a collection."""
        collection = self.get_collection(collection_name)
        kwargs = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)
        return results

    def search_by_symbol(
        self,
        collection_name: str,
        symbol: str,
        query: str,
        n_results: int = 5,
    ) -> dict:
        """Search within a specific stock's documents."""
        return self.search(
            collection_name,
            query,
            n_results=n_results,
            where={"symbol": symbol},
        )

    def count(self, collection_name: str) -> int:
        collection = self.get_collection(collection_name)
        return collection.count()

    def delete_collection(self, name: str):
        try:
            self._client.delete_collection(name)
        except Exception:
            pass
