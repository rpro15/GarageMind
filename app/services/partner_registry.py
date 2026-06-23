from __future__ import annotations

from app.domain.models import Partner, Product

STUB_PARTNERS: list[Partner] = [
    Partner(
        id="partner_ozon",
        name="Ozon",
        affiliate_enabled=True,
        priority_weight=0.9,
        base_url="https://ozon.ru",
        affiliate_tag="garagemind_ozon",
    ),
    Partner(
        id="partner_wb",
        name="Wildberries",
        affiliate_enabled=True,
        priority_weight=0.7,
        base_url="https://wildberries.ru",
        affiliate_tag="garagemind_wb",
    ),
    Partner(
        id="partner_avito",
        name="Avito",
        affiliate_enabled=False,
        priority_weight=0.3,
        base_url="https://avito.ru",
        affiliate_tag=None,
    ),
]

STUB_PRODUCTS: list[Product] = [
    # Tires
    Product(
        id="tire_001",
        partner_id="partner_ozon",
        name="Nokian Tyres Hakkapeliitta 10 205/55 R16",
        category="tires",
        price=8500.0,
        image_url=None,
        description="Winter studded tire, excellent grip on ice",
    ),
    Product(
        id="tire_002",
        partner_id="partner_wb",
        name="Michelin Pilot Sport 4 225/45 R17",
        category="tires",
        price=11200.0,
        image_url=None,
        description="High-performance summer tire",
    ),
    Product(
        id="tire_003",
        partner_id="partner_avito",
        name="Bridgestone Ecopia EP150 195/65 R15",
        category="tires",
        price=5900.0,
        image_url=None,
        description="Fuel-efficient all-season tire",
    ),
    # Wheels
    Product(
        id="wheel_001",
        partner_id="partner_ozon",
        name="Replica OEM Alloy Wheel 16x6.5 ET38",
        category="wheels",
        price=4200.0,
        image_url=None,
        description="OEM-style alloy wheel, 5x114.3 PCD",
    ),
    Product(
        id="wheel_002",
        partner_id="partner_wb",
        name="Enkei RPF1 17x8 ET35",
        category="wheels",
        price=9800.0,
        image_url=None,
        description="Lightweight forged racing wheel",
    ),
    Product(
        id="wheel_003",
        partner_id="partner_avito",
        name="Stilauto SR700 15x6 ET43",
        category="wheels",
        price=3100.0,
        image_url=None,
        description="Budget steel wheel with gloss finish",
    ),
]


class PartnerRegistry:
    """Holds the partner and product catalog.

    In the MVP this is seeded from the stub constants above.
    Future iterations can replace the constructor with a DB-backed loader.
    """

    def __init__(
        self,
        partners: list[Partner] | None = None,
        products: list[Product] | None = None,
    ) -> None:
        self._partners: dict[str, Partner] = {
            p.id: p for p in (partners if partners is not None else STUB_PARTNERS)
        }
        self._products: list[Product] = (
            products if products is not None else list(STUB_PRODUCTS)
        )

    def get_partner(self, partner_id: str) -> Partner | None:
        return self._partners.get(partner_id)

    def list_partners(self) -> list[Partner]:
        return list(self._partners.values())

    def list_products(self, category: str | None = None) -> list[Product]:
        if category is None:
            return list(self._products)
        return [p for p in self._products if p.category == category]
