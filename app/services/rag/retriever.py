import logging
from typing import List, Dict, Any, Optional

from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import VectorStore
from app.domain.models import Product

logger = logging.getLogger(__name__)


class Retriever:
    """
    RAG-ретривер: эмбеддинг запроса → поиск по ChromaDB → возврат товаров.
    """

    def __init__(self, embedding: EmbeddingService, store: VectorStore):
        self._embedding = embedding
        self._store = store

    async def search_products(
        self,
        query: str,
        brand: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Product]:
        """Ищет товары, семантически похожие на запрос."""
        emb = await self._embedding.embed(query)

        text_filter = None
        if brand:
            text_filter = {"brand": brand.lower()}

        results = self._store.hybrid_search(
            query_embedding=emb,
            text_filter=text_filter,
            top_k=top_k,
        )

        products = []
        for r in results:
            meta = r["metadata"]
            products.append(Product(
                id=r["id"],
                name=meta.get("name", r["document"][:50]),
                price=float(meta.get("price", 0)),
                currency=meta.get("currency", "RUB"),
                image_url=meta.get("image_url"),
                partner_link=meta.get("partner_link"),
                source=meta.get("source", "unknown"),
                rating=float(meta["rating"]) if meta.get("rating") else None,
            ))
        return products

    async def index_products(self, products: List[Product]) -> int:
        """Индексирует список товаров в векторную базу."""
        if not products:
            return 0

        texts = []
        ids = []
        metadatas = []

        for p in products:
            text = (
                f"Шина {p.name}. "
                f"Цена: {p.price} {p.currency}. "
                f"Рейтинг: {p.rating or 'нет'}. "
                f"Источник: {p.source or 'неизвестно'}."
            )
            ids.append(p.id)
            texts.append(text)
            metadatas.append({
                "name": p.name,
                "price": p.price,
                "currency": p.currency,
                "image_url": p.image_url or "",
                "partner_link": p.partner_link or "",
                "source": p.source or "",
                "rating": p.rating or 0.0,
                "brand": "",
            })

        embs = await self._embedding.embed_batch(texts)
        self._store.add_products(ids=ids, embeddings=embs, metadatas=metadatas, documents=texts)
        return len(ids)
