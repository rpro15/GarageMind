import logging
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


class VectorStore:
    """Векторное хранилище на ChromaDB."""

    def __init__(self, persist_dir: str = "data/chromadb"):
        os.makedirs(persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="tire_products",
            metadata={"hnsw:space": "cosine"},
        )

    def add_products(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str],
    ) -> None:
        """Добавить товары в векторную базу."""
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )
        logger.info("Added %d products to vector store", len(ids))

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Поиск по вектору. Возвращает список товаров с расстояниями."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        if not results["ids"] or not results["ids"][0]:
            return []

        items = []
        for i, doc_id in enumerate(results["ids"][0]):
            items.append({
                "id": doc_id,
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return items

    def hybrid_search(
        self,
        query_embedding: List[float],
        text_filter: Optional[Dict[str, str]] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Гибридный поиск: векторный + фильтр по метаданным."""
        where = None
        if text_filter:
            where = {}
            for key, value in text_filter.items():
                where[key] = value
        return self.search(query_embedding, top_k=top_k, where=where)

    def count(self) -> int:
        return self._collection.count()

    def delete_collection(self):
        try:
            self._client.delete_collection("tire_products")
        except Exception:
            pass
