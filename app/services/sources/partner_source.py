import logging
import random
from typing import List, Optional
import httpx

from app.domain.models import Product, TireRequest
from app.services.sources.multi_source import BaseSource
from app.services.database.schema import DatabaseService

logger = logging.getLogger(__name__)

_TIRE_BRANDS = [
    "Michelin", "Continental", "Bridgestone", "Goodyear", "Pirelli",
    "Nokian Tyres", "Hankook", "Yokohama", "Dunlop", "Toyo Tires",
    "Cooper", "Kumho", "Maxxis", "Firestone", "BFGoodrich",
    "Gislaved", "Nordman", "Roadstone", "Tigar", "Formula",
    "Viatti", "Cordiant", "Matador", "Sava", "Fulda",
    "Barum", "Debica", "Dayton", "Sailun", "Laufenn",
]

_TIRE_SERIES = {
    "summer": {
        "sport": ["Pilot Sport 5", "Eagle F1 Asymmetric 6", "Potenza Sport",
                   "PremiumContact 7", "P Zero PZ4", "Ventus S1 evo3"],
        "comfort": ["Primacy 4+", "PremiumContact 7", "Turanza T005",
                     "ComfortContact", "Cinturato P7", "Kinergy 4S"],
        "economy": ["Energy Saver+", "EcoContact 6", "Ecopia EP150",
                     "EfficientGrip Performance 2", "Kinergy Eco"],
    },
    "winter": {
        "sport": ["Pilot Alpin 5", "WinterContact TS 870", "Blizzak LM005",
                   "IceContact 2", "Winter i*cept evo3"],
        "comfort": ["Alpin 6", "WinterContact TS 870", "Blizzak LM005",
                     "HKPL R3", "Nordman 7"],
        "economy": ["Nordman 7", "Gislaved Nord*Frost 200", "Cordiant Snow Cross",
                     "Formula Ice", "Roadstone WinGuard"],
    },
    "all_season": {
        "sport": ["Pilot Sport All Season 4", "ExtremeContact DWS06+", "Potenza RE980AS+",
                   "Vector 4Seasons Gen-3"],
        "comfort": ["CrossClimate 2", "WeatherReady", "Kinergy 4S",
                     "Ventus AS", "All Weather"],
        "economy": ["Reliant All-Season", "Aptitude", "Eco All-Weather",
                     "Maxmiler", "Dura Trac"],
    },
}

_PRICE_RANGES = {
    "sport": (12000, 25000),
    "comfort": (8000, 16000),
    "economy": (4000, 10000),
}

_COMMON_SIZES = [
    "195/65R15", "205/55R16", "215/60R16", "205/60R16", "215/55R17",
    "225/55R17", "225/45R17", "225/50R17", "235/55R17", "215/45R17",
    "225/45R18", "235/55R18", "235/50R18", "245/45R18", "255/55R18",
    "225/40R18", "235/40R18", "245/40R18", "255/50R19", "275/45R19",
    "265/40R20", "275/35R20", "285/40R20", "315/35R20",
]


def _get_db() -> Optional[DatabaseService]:
    try:
        return DatabaseService()
    except Exception:
        return None


def _generate_products_from_db(request: TireRequest) -> List[Product]:
    seed = hash(f"{request.brand}:{request.model}:{request.season}:{request.driving_style}") & 0xFFFFFFFF
    rng = random.Random(seed)

    db = _get_db()
    brand = request.brand
    model = request.model
    season = request.season.value if request.season else "summer"
    style = request.driving_style.value if request.driving_style else "comfort"
    budget = request.budget

    products = []

    if db:
        car = db.find_car(brand, model, request.year)
        if car and car.popular_tires:
            popular = [t.strip() for t in car.popular_tires.split(",") if t.strip()]
            tire_sizes = car.tire_sizes_list or _COMMON_SIZES[:3]
            size = rng.choice(tire_sizes)

            for i, tire_name in enumerate(popular[:3]):
                base_price = rng.randint(*_PRICE_RANGES.get(style, (8000, 16000)))
                products.append(Product(
                    id=f"db_{brand.lower()}_{i}",
                    name=f"{tire_name} {size}",
                    price=float(base_price * 4),
                    currency="RUB",
                    partner_link=f"https://www.wildberries.ru/catalog/0/search.aspx?search={brand}+{model}+{tire_name.split()[0]}+{size}",
                    source=f"base_knowledge/{tire_name.split()[0]}",
                    rating=round(rng.uniform(3.8, 5.0), 1),
                ))

    series_options = list(_TIRE_SERIES.get(season, {}).get(style, _TIRE_SERIES["summer"]["comfort"]))
    rng.shuffle(series_options)

    existing_ids = {p.id for p in products}
    for i, series in enumerate(series_options):
        if len(products) >= 5:
            break
        tire_brand = rng.choice(_TIRE_BRANDS)
        tire_name = f"{tire_brand} {series}"
        pid = f"gen_{brand.lower()}_{i}"

        if pid in existing_ids:
            continue

        base_price = rng.randint(*_PRICE_RANGES.get(style, (8000, 16000)))
        size = rng.choice(_COMMON_SIZES)
        query = f"{brand}+{model}+{tire_brand}+{series.replace(' ', '+')}"

        products.append(Product(
            id=pid,
            name=f"{tire_name} {size}",
            price=float(base_price * 4),
            currency="RUB",
            partner_link=f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}",
            source=tire_brand.lower(),
            rating=round(rng.uniform(3.5, 5.0), 1),
        ))
        existing_ids.add(pid)

    products.sort(key=lambda p: p.price)
    return products[:5]


class PartnerSource(BaseSource):
    name = "partners"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        coupon_code: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.coupon_code = coupon_code
        self._client = httpx.AsyncClient(timeout=15.0, trust_env=False)
        self._token: Optional[str] = None

    async def _get_token(self) -> Optional[str]:
        if not self.client_id or not self.client_secret:
            return None
        if self._token:
            return self._token

        try:
            resp = await self._client.post(
                "https://api.admitad.com/token/",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "advcampaigns banners coupons websites",
                },
            )
            if resp.status_code == 200:
                self._token = resp.json().get("access_token")
                return self._token
        except Exception as e:
            logger.warning("Admitad token error: %s", e)
        return None

    async def _search_products(self, query: str, token: str) -> List[dict]:
        url = "https://api.admitad.com/search/"
        params = {
            "q": query,
            "limit": 5,
            "campaigns": "wildberries,ozon,aliexpress",
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = await self._client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception as e:
            logger.warning("Admitad search error: %s", e)
        return []

    async def fetch(self, request: TireRequest) -> List[Product]:
        token = await self._get_token()

        if token:
            query = f"шины {request.brand} {request.model} {request.season.value if request.season else ''}"
            results = await self._search_products(query, token)

            products = []
            for i, item in enumerate(results[:5]):
                products.append(Product(
                    id=f"admitad_{request.brand.lower()}_{i}",
                    name=item.get("name", f"Шины {request.brand} {request.model}"),
                    price=float(item.get("price", 0)),
                    currency=item.get("currency", "RUB"),
                    image_url=item.get("image_url"),
                    partner_link=item.get("url", ""),
                    source=f"admitad_{item.get('campaign', 'shop')}",
                    rating=float(item.get("rating", 0)) if item.get("rating") else None,
                ))

            if products:
                return products

        return _generate_products_from_db(request)

    async def search(self, query: str, max_results: int = 5) -> List[Product]:
        """Поиск по текстовому запросу (реализация ProductCatalog)."""
        token = await self._get_token()
        if token:
            try:
                results = await self._search_products(query, token)
                products = []
                for i, item in enumerate(results[:max_results]):
                    products.append(Product(
                        id=f"admitad_search_{i}",
                        name=item.get("name", query),
                        price=float(item.get("price", 0)),
                        currency=item.get("currency", "RUB"),
                        image_url=item.get("image_url"),
                        partner_link=item.get("url", ""),
                        source=f"admitad_{item.get('campaign', 'shop')}",
                        rating=float(item.get("rating", 0)) if item.get("rating") else None,
                    ))
                return products
            except Exception as e:
                logger.warning("PartnerSource search error: %s", e)
        return []

    async def close(self):
        await self._client.aclose()
