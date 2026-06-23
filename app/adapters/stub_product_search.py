from __future__ import annotations

from app.domain.models import ProductRecommendation, RecommendRequest
from app.ports.product_search import ProductSearchProvider

# Stub product catalog – replace with real marketplace API adapters later.
# Keys: category, season (None = applies to all seasons), driving_style (None = all styles),
#       max_price_rub (None = no upper limit).
_CATALOG: list[dict] = [
    # --- Tires: winter ---
    {
        "product_name": "Pirelli Ice Zero 195/65 R15",
        "category": "tires",
        "season": "winter",
        "driving_style": None,
        "price_rub": 6500,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Pirelli+Ice+Zero+195%2F65+R15&partner=STUB",
        "image_url": "https://cdn.stub.example/pirelli-ice-zero.jpg",
    },
    {
        "product_name": "Nokian Hakkapeliitta R5 205/55 R16",
        "category": "tires",
        "season": "winter",
        "driving_style": None,
        "price_rub": 8900,
        "marketplace": "wildberries",
        "affiliate_url": "https://wildberries.ru/catalog/0/search.aspx?search=Nokian+Hakkapeliitta+R5&partner=STUB",
        "image_url": "https://cdn.stub.example/nokian-hakk-r5.jpg",
    },
    {
        "product_name": "Michelin X-Ice North 4 215/60 R16",
        "category": "tires",
        "season": "winter",
        "driving_style": None,
        "price_rub": 9800,
        "marketplace": "yandex_market",
        "affiliate_url": "https://market.yandex.ru/search?text=Michelin+X-Ice+North+4&partner=STUB",
        "image_url": "https://cdn.stub.example/michelin-x-ice-north4.jpg",
    },
    {
        "product_name": "Bridgestone Blizzak DM-V3 225/60 R17",
        "category": "tires",
        "season": "winter",
        "driving_style": None,
        "price_rub": 11200,
        "marketplace": "admitad",
        "affiliate_url": "https://autodoc.ru/search?q=Bridgestone+Blizzak+DM-V3&partner=STUB",
        "image_url": "https://cdn.stub.example/bridgestone-blizzak.jpg",
    },
    {
        "product_name": "Yokohama IceGuard IG65 195/65 R15",
        "category": "tires",
        "season": "winter",
        "driving_style": None,
        "price_rub": 5800,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Yokohama+IceGuard+IG65&partner=STUB",
        "image_url": "https://cdn.stub.example/yokohama-iceguard.jpg",
    },
    # --- Tires: summer / comfort ---
    {
        "product_name": "Michelin Primacy 4 205/55 R16",
        "category": "tires",
        "season": "summer",
        "driving_style": "comfort",
        "price_rub": 7400,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Michelin+Primacy+4&partner=STUB",
        "image_url": "https://cdn.stub.example/michelin-primacy4.jpg",
    },
    {
        "product_name": "Continental ComfortContact CC6 195/65 R15",
        "category": "tires",
        "season": "summer",
        "driving_style": "comfort",
        "price_rub": 5900,
        "marketplace": "wildberries",
        "affiliate_url": "https://wildberries.ru/catalog/0/search.aspx?search=Continental+ComfortContact+CC6&partner=STUB",
        "image_url": "https://cdn.stub.example/continental-cc6.jpg",
    },
    # --- Tires: summer / sport ---
    {
        "product_name": "Bridgestone Potenza Sport 225/45 R18",
        "category": "tires",
        "season": "summer",
        "driving_style": "sport",
        "price_rub": 12500,
        "marketplace": "admitad",
        "affiliate_url": "https://exist.ru/search/?q=Bridgestone+Potenza+Sport&partner=STUB",
        "image_url": "https://cdn.stub.example/bridgestone-potenza.jpg",
    },
    {
        "product_name": "Pirelli P Zero 245/40 R19",
        "category": "tires",
        "season": "summer",
        "driving_style": "sport",
        "price_rub": 18000,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Pirelli+P+Zero+245%2F40+R19&partner=STUB",
        "image_url": "https://cdn.stub.example/pirelli-pzero.jpg",
    },
    # --- Tires: all_season ---
    {
        "product_name": "Goodyear Vector 4Seasons Gen-3 205/55 R16",
        "category": "tires",
        "season": "all_season",
        "driving_style": None,
        "price_rub": 8200,
        "marketplace": "wildberries",
        "affiliate_url": "https://wildberries.ru/catalog/0/search.aspx?search=Goodyear+Vector+4Seasons&partner=STUB",
        "image_url": "https://cdn.stub.example/goodyear-vector.jpg",
    },
    {
        "product_name": "Michelin CrossClimate 2 195/65 R15",
        "category": "tires",
        "season": "all_season",
        "driving_style": None,
        "price_rub": 7600,
        "marketplace": "yandex_market",
        "affiliate_url": "https://market.yandex.ru/search?text=Michelin+CrossClimate+2&partner=STUB",
        "image_url": "https://cdn.stub.example/michelin-crossclimate2.jpg",
    },
    # --- Tires: offroad ---
    {
        "product_name": "BFGoodrich Mud-Terrain T/A KM3 265/70 R17",
        "category": "tires",
        "season": "summer",
        "driving_style": "offroad",
        "price_rub": 14500,
        "marketplace": "admitad",
        "affiliate_url": "https://autodoc.ru/search?q=BFGoodrich+Mud-Terrain+KM3&partner=STUB",
        "image_url": "https://cdn.stub.example/bfgoodrich-km3.jpg",
    },
    {
        "product_name": "Yokohama Geolandar M/T G003 265/65 R17",
        "category": "tires",
        "season": "all_season",
        "driving_style": "offroad",
        "price_rub": 11800,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Yokohama+Geolandar+M%2FT&partner=STUB",
        "image_url": "https://cdn.stub.example/yokohama-geolandar.jpg",
    },
    # --- Wheels (discs) ---
    {
        "product_name": "Диски литые КиК Тайга 7Jx16 5x114.3 ET45",
        "category": "wheels",
        "season": None,
        "driving_style": None,
        "price_rub": 4200,
        "marketplace": "wildberries",
        "affiliate_url": "https://wildberries.ru/catalog/0/search.aspx?search=КиК+Тайга+7Jx16&partner=STUB",
        "image_url": "https://cdn.stub.example/kik-tayga.jpg",
    },
    {
        "product_name": "Диски штампованные Sinkomer 6.5Jx16 5x114.3",
        "category": "wheels",
        "season": None,
        "driving_style": None,
        "price_rub": 1800,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Sinkomer+6.5Jx16&partner=STUB",
        "image_url": "https://cdn.stub.example/sinkomer.jpg",
    },
    {
        "product_name": "Диски легкосплавные NZ Wheels F-23 7Jx17 5x112",
        "category": "wheels",
        "season": None,
        "driving_style": "comfort",
        "price_rub": 5600,
        "marketplace": "yandex_market",
        "affiliate_url": "https://market.yandex.ru/search?text=NZ+Wheels+F-23+7Jx17&partner=STUB",
        "image_url": "https://cdn.stub.example/nz-wheels-f23.jpg",
    },
    {
        "product_name": "Диски кованые K&K Байкал 8Jx18 5x114.3 ET35",
        "category": "wheels",
        "season": None,
        "driving_style": "sport",
        "price_rub": 9800,
        "marketplace": "admitad",
        "affiliate_url": "https://autodoc.ru/search?q=K%26K+Байкал+8Jx18&partner=STUB",
        "image_url": "https://cdn.stub.example/kk-baikal.jpg",
    },
    {
        "product_name": "Диски стальные Legeartis Concept 6.5Jx16 5x108",
        "category": "wheels",
        "season": None,
        "driving_style": None,
        "price_rub": 2400,
        "marketplace": "wildberries",
        "affiliate_url": "https://wildberries.ru/catalog/0/search.aspx?search=Legeartis+Concept+6.5Jx16&partner=STUB",
        "image_url": "https://cdn.stub.example/legeartis-concept.jpg",
    },
    {
        "product_name": "Диски литые Remain Aurus 7Jx17 5x114.3",
        "category": "wheels",
        "season": None,
        "driving_style": "offroad",
        "price_rub": 6700,
        "marketplace": "ozon",
        "affiliate_url": "https://ozon.ru/search/?text=Remain+Aurus+7Jx17&partner=STUB",
        "image_url": "https://cdn.stub.example/remain-aurus.jpg",
    },
]

_MAX_RESULTS = 4


def _score(item: dict, request: RecommendRequest) -> float:
    """Return a relevance score; higher is better. Items that do not match
    mandatory filters receive -1 (excluded)."""
    if item["category"] != request.category:
        return -1.0

    # Season filter: item season must match request or be None (universal).
    if item["season"] is not None and item["season"] != request.season:
        return -1.0

    # Style filter: item style must match request or be None (universal).
    if item["driving_style"] is not None and item["driving_style"] != request.driving_style:
        return -1.0

    # Budget filter.
    if item["price_rub"] > request.budget_rub:
        return -1.0

    score = 0.0

    # Prefer exact season match over universal items.
    if item["season"] == request.season:
        score += 1.0

    # Prefer exact style match.
    if item["driving_style"] == request.driving_style:
        score += 1.0

    # Prefer items closer to (but not over) the budget ceiling – value for money.
    score += item["price_rub"] / max(request.budget_rub, 1)

    return score


class StubProductSearchProvider(ProductSearchProvider):
    def search(self, request: RecommendRequest) -> list[ProductRecommendation]:
        scored = [
            (item, _score(item, request))
            for item in _CATALOG
        ]
        eligible = [(item, s) for item, s in scored if s >= 0]
        eligible.sort(key=lambda x: x[1], reverse=True)

        results: list[ProductRecommendation] = []
        for rank, (item, _) in enumerate(eligible[:_MAX_RESULTS], start=1):
            results.append(
                ProductRecommendation(
                    rank=rank,
                    product_name=item["product_name"],
                    category=item["category"],
                    season=item["season"] or request.season,
                    price_rub=item["price_rub"],
                    marketplace=item["marketplace"],
                    affiliate_url=item["affiliate_url"],
                    image_url=item["image_url"],
                    is_partner=False,  # set by service after partner prioritisation
                    source="stub",
                )
            )
        return results
