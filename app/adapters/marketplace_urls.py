from __future__ import annotations

"""Marketplace adapter helpers.

Each function builds a properly-formatted affiliate URL for the given
marketplace.  Partner / affiliate IDs are read from env vars and passed in
by ``build_recommendation_service``.  Replace the stub search URLs with real
product-API calls once you have approved API access.
"""

import urllib.parse


def ozon_affiliate_url(product_name: str, partner_id: str) -> str:
    """Ozon partner search URL.

    Real integration: POST https://api-seller.ozon.ru/v1/product/search
    with ******; use the returned product URL + partner tag.
    """
    query = urllib.parse.quote(product_name)
    return f"https://ozon.ru/search/?text={query}&partner={partner_id}"


def wildberries_affiliate_url(product_name: str, partner_id: str) -> str:
    """Wildberries affiliate search URL.

    Real integration: WB does not have a public search API; use their
    affiliate deep-link generator at https://cpa.wildberries.ru/tools/deeplinks
    """
    query = urllib.parse.quote(product_name)
    return (
        f"https://www.wildberries.ru/catalog/0/search.aspx"
        f"?search={query}&affiliate_id={partner_id}"
    )


def admitad_affiliate_url(product_name: str, partner_id: str, campaign_id: str) -> str:
    """Admitad deep-link for autodoc.ru (or any other Admitad store).

    Real integration: POST https://api.admitad.com/deeplink/{campaign_id}/
    with OAuth2 token; returns a tracked deep-link.
    """
    query = urllib.parse.quote(product_name)
    return (
        f"https://ad.admitad.com/g/{campaign_id}/"
        f"?ulp=https://autodoc.ru/search%3Fq%3D{query}"
        f"&partner={partner_id}"
    )


def yandex_market_affiliate_url(product_name: str, partner_id: str) -> str:
    """Yandex Market affiliate search URL.

    Real integration: GET https://api.partner.market.yandex.ru/v2/search/...
    with OAuth2; use the returned offer URL + clid parameter.
    """
    query = urllib.parse.quote(product_name)
    return f"https://market.yandex.ru/search?text={query}&clid={partner_id}"
