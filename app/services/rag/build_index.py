"""
Скрипт для построения векторного индекса товаров в ChromaDB.

Запуск:
    python3 -m app.services.rag.build_index

Что делает:
1. Берёт все названия шин из SQLite (отзывы, проблемы, спецификации, популярные)
2. Берёт товары из словаря KNOWN_TIRES и _TIRE_SERIES
3. Генерирует эмбеддинги через DeepSeek API
4. Сохраняет в ChromaDB (папка data/chromadb/)
"""
import asyncio
import logging
import random
from typing import List

from app.services.database.schema import DatabaseService
from app.services.rag import EmbeddingService, VectorStore, Retriever
from app.domain.models import Product

logger = logging.getLogger(__name__)

# Источники названий шин
TIRE_NAMES = [
    # Michelin
    "Michelin Pilot Sport 4", "Michelin Pilot Sport 5", "Michelin Primacy 4+",
    "Michelin Latitude Sport 3", "Michelin Energy Saver+", "Michelin Alpin 6",
    "Michelin Pilot Alpin 5", "Michelin CrossClimate 2", "Michelin Pilot Sport All Season 4",
    # Continental
    "Continental PremiumContact 6", "Continental PremiumContact 7",
    "Continental EcoContact 6", "Continental WinterContact TS 870",
    "Continental CrossContact LX Sport", "Continental ExtremeContact DWS06+",
    "Continental CrossClimate 2", "Continental VikingContact 7",
    # Bridgestone
    "Bridgestone Turanza T005", "Bridgestone Potenza Sport",
    "Bridgestone Alenza 001", "Bridgestone Dueler H/P Sport",
    "Bridgestone Blizzak LM005", "Bridgestone Ecopia EP150",
    # Nokian
    "Nokian Hakka Green 3", "Nokian Hakka Blue 3",
    "Nokian Nordman 7", "Nokian Nordman 8",
    "Nokian Hakkapeliitta R3", "Nokian Hakkapeliitta R5",
    # Hankook
    "Hankook Kinergy Eco 2", "Hankook Ventus S1 evo3",
    "Hankook Ventus S1 evo2", "Hankook Kinergy 4S",
    # Pirelli
    "Pirelli P Zero PZ4", "Pirelli Cinturato P7",
    "Pirelli Scorpion Verde All Season", "Pirelli Winter Sottozero 3",
    # Goodyear
    "Goodyear Eagle F1 Asymmetric 5", "Goodyear Eagle F1 Asymmetric 6",
    "Goodyear EfficientGrip Performance 2", "Goodyear Wrangler AT Adventure",
    "Goodyear Vector 4Seasons Gen-3", "Goodyear UltraGrip Performance 3",
    # Yokohama
    "Yokohama Advan Sport V105", "Yokohama BlueEarth AE51",
    "Yokohama Geolandar X-CV", "Yokohama IceGuard IG60",
    # Dunlop
    "Dunlop SP Sport Maxx 050", "Dunlop Sport BluResponse",
    "Dunlop Grandtrek PT3A", "Dunlop Winter Sport 5",
    # Toyo
    "Toyo Proxes Sport", "Toyo Proxes CF2",
    "Toyo Celsius All Season", "Toyo Observe G3-Ice",
    # Cooper
    "Cooper Zeon RS3-G1", "Cooper Discoverer AT3 4S",
    "Cooper CS5 Ultra Touring", "Cooper Evolution Winter",
    # Maxxis
    "Maxxis Premitra HP5", "Maxxis Bravo HP-M3",
    "Maxxis Arctic Trevader", "Maxxis RAZR AT811",
    # Gislaved
    "Gislaved Nord*Frost 200", "Gislaved Ultra*Frost 200",
    "Gislaved Control M+S", "Gislaved Super Winter",
    # Viatti
    "Viatti Strada Asimmetrico", "Viatti Bosco A/T",
    "Viatti Vettore Inverno", "Viatti Strada Radial",
    # Cordiant
    "Cordiant Sport 3", "Cordiant Road Runner",
    "Cordiant Snow Cross", "Cordiant Professional",
    # Nordman
    "Nordman 7", "Nordman 8", "Nordman SX2", "Nordman RS2",
    # Formula
    "Formula Energy", "Formula Ice", "Formula Winter",
    "Formula Performance", "Formula Comfort",
    # Barum
    "Barum Bravuris 5HM", "Barum Polaris 5",
    "Barum Quartaris 5", "Barum Vanis",
    # Sava
    "Sava Intensa HP2", "Sava Eskimo HP2",
    "Sava All Weather", "Sava Adapta",
    # Falken
    "Falken Azenis FK520", "Falken Wildpeak A/T3W",
    "Falken Sincera SN832", "Falken EuroWinter HS449",
    # Laufenn
    "Laufenn S-Fit EQ", "Laufenn I-Fit LW51",
    "Laufenn X-Fit Van", "Laufenn D-Use 4S",
    # Kumho
    "Kumho Ecsta PS71", "Kumho Solus TA31",
    "Kumho Road Venture AT52", "Kumho WinterCraft WP71",
]

# Размеры шин (подставляются к названию)
SIZES = [
    "195/65R15", "205/55R16", "215/60R16", "205/60R16",
    "215/55R17", "225/55R17", "225/45R17", "235/55R17",
    "225/45R18", "235/55R18", "235/50R18", "245/45R18",
    "255/55R18", "225/40R18", "235/40R18", "245/40R18",
    "255/50R19", "275/45R19", "265/40R20", "275/35R20",
    "285/40R20", "315/35R20", "215/65R16", "225/65R17",
    "235/55R19", "185/65R15", "195/55R16", "205/50R17",
]

# Диапазоны цен (₽ за комплект, 4 шт.)
PRICE_RANGES = {
    "premium": (40000, 80000),
    "mid": (20000, 40000),
    "budget": (8000, 20000),
}


def _get_db_names(db: DatabaseService) -> List[str]:
    """Собрать названия шин из SQLite."""
    names = set()

    # Из отзывов
    with db._conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT tire_name FROM tire_reviews WHERE tire_name != ''"
        ).fetchall()
        for r in rows:
            names.add(r["tire_name"])

    # Из проблем
    with db._conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT tire_name FROM tire_problems WHERE tire_name != ''"
        ).fetchall()
        for r in rows:
            names.add(r["tire_name"])

    # Из спецификаций
    with db._conn() as conn:
        rows = conn.execute(
            "SELECT name FROM tire_specs WHERE name != ''"
        ).fetchall()
        for r in rows:
            names.add(r["name"])

    # Из popular_tires
    with db._conn() as conn:
        rows = conn.execute(
            "SELECT popular_tires FROM car_models WHERE popular_tires != ''"
        ).fetchall()
        for r in rows:
            for t in r["popular_tires"].split(","):
                t = t.strip()
                if t:
                    names.add(t)

    return list(names)


def _build_products(db_names: List[str]) -> List[Product]:
    """Создать список Product для индексации."""
    all_names = list(set(db_names + TIRE_NAMES))
    random.shuffle(all_names)
    products = []

    for i, name in enumerate(all_names[:300]):  # лимит 300
        price_range = PRICE_RANGES["mid"]
        if any(w in name.lower() for w in ["pilot sport", "p zero", "eagle f1", "potenza sport"]):
            price_range = PRICE_RANGES["premium"]
        elif any(w in name.lower() for w in ["energy", "eco", "kinergy eco", "sincera"]):
            price_range = PRICE_RANGES["budget"]

        size = random.choice(SIZES)
        full_name = f"{name} {size}"
        price = round(random.uniform(*price_range), -2)  # округление до сотен
        brand = name.split()[0] if name else ""

        products.append(Product(
            id=f"idx_{i}",
            name=full_name,
            price=price,
            currency="RUB",
            image_url="",
            partner_link="",
            source=brand.lower() if brand else "unknown",
            rating=round(random.uniform(3.0, 5.0), 1),
        ))

    return products


async def build_index():
    """Построить векторный индекс товаров в ChromaDB."""
    logger.info("🔨 Построение векторного индекса товаров...")

    db = DatabaseService()
    emb = EmbeddingService()
    store = VectorStore()
    retriever = Retriever(emb, store)

    # Удаляем старую коллекцию
    store.delete_collection()
    # Создаём заново (инициализация через get_or_create_collection)
    store._collection = store._client.get_or_create_collection(
        name="tire_products",
        metadata={"hnsw:space": "cosine"},
    )

    # Собираем названия из БД + словаря
    db_names = _get_db_names(db)
    products = _build_products(db_names)

    logger.info(f"📦 Всего товаров для индексации: {len(products)}")

    # Индексируем батчами по 10 (чтобы не превысить лимиты DeepSeek API)
    batch_size = 10
    total_indexed = 0

    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        try:
            count = await retriever.index_products(batch)
            total_indexed += count
            logger.info(f"  ➕ Проиндексировано {total_indexed}/{len(products)}...")
        except Exception as e:
            logger.warning(f"  ⚠️ Ошибка батча {i}: {e}")
            continue

    final_count = store.count()
    logger.info(f"✅ Готово! ChromaDB содержит {final_count} товаров.")
    logger.info(f"   Путь: data/chromadb/")

    return final_count


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    count = asyncio.run(build_index())
    print(f"\n🎉 ChromaDB проиндексирована: {count} товаров")


if __name__ == "__main__":
    main()
