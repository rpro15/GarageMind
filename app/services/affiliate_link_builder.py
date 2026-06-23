from __future__ import annotations

from urllib.parse import urlencode, urljoin

from app.domain.models import Partner, Product


class AffiliateLinkBuilder:
    """Builds an outbound URL for a product, injecting the affiliate tag when available."""

    def build(self, product: Product, partner: Partner) -> str:
        path = f"/catalog/{product.id}"
        base = urljoin(partner.base_url, path)
        if partner.affiliate_enabled and partner.affiliate_tag:
            params = urlencode({"ref": partner.affiliate_tag})
            return f"{base}?{params}"
        return base
