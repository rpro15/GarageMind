from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error

from app.domain.models import ProductRecommendation, RecommendRequest
from app.ports.product_search import ProductSearchProvider

_DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
_MODEL = "deepseek-chat"
_MAX_RESULTS = 4

_SYSTEM_PROMPT = (
    "Ты — автоэксперт AI-помощник GarageMind. "
    "Ты подбираешь шины и диски для автомобилей с учётом сезона, стиля вождения и бюджета. "
    "Отвечай строго в формате JSON-массива без дополнительного текста."
)

_USER_PROMPT_TEMPLATE = (
    "Подбери {count} варианта {category_ru} для {make} {model} {year} года. "
    "Сезон: {season_ru}. Стиль вождения: {style_ru}. Бюджет: до {budget} руб. "
    "Для каждого варианта верни JSON-объект с полями: "
    "product_name (строка), price_rub (целое число), marketplace (одно из: ozon, wildberries, yandex_market, admitad). "
    "Верни только массив JSON, без markdown и объяснений."
)

_CATEGORY_RU = {"tires": "шин", "wheels": "дисков"}
_SEASON_RU = {"winter": "зима", "summer": "лето", "all_season": "всесезон"}
_STYLE_RU = {"comfort": "комфорт", "sport": "спорт", "offroad": "бездорожье"}


def _build_affiliate_url(marketplace: str, product_name: str, partner_id: str) -> str:
    query = urllib.request.quote(product_name)
    if marketplace == "ozon":
        return f"https://ozon.ru/search/?text={query}&partner={partner_id}"
    if marketplace == "wildberries":
        return f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}&affiliate_id={partner_id}"
    if marketplace == "yandex_market":
        return f"https://market.yandex.ru/search?text={query}&partner={partner_id}"
    # admitad / default
    return f"https://autodoc.ru/search?q={query}&partner={partner_id}"


class DeepSeekProductSearchProvider(ProductSearchProvider):
    """Calls the DeepSeek API to generate smart product recommendations.

    Falls back to the stub provider if the API key is unavailable or the
    request fails.
    """

    def __init__(
        self,
        api_key: str,
        partner_id: str = "GARAGEMIND",
        logger: logging.Logger | None = None,
    ) -> None:
        self._api_key = api_key
        self._partner_id = partner_id
        self._logger = logger or logging.getLogger(__name__)

    def search(self, request: RecommendRequest) -> list[ProductRecommendation]:
        prompt = _USER_PROMPT_TEMPLATE.format(
            count=_MAX_RESULTS,
            category_ru=_CATEGORY_RU.get(request.category, request.category),
            make=request.car_make,
            model=request.car_model,
            year=request.car_year,
            season_ru=_SEASON_RU.get(request.season, request.season),
            style_ru=_STYLE_RU.get(request.driving_style, request.driving_style),
            budget=request.budget_rub,
        )

        body = json.dumps(
            {
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 512,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            _DEEPSEEK_API_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self._api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            self._logger.warning("DeepSeek API request failed: %s", exc)
            return self._fallback(request)

        try:
            content = data["choices"][0]["message"]["content"].strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            items: list[dict] = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            self._logger.warning("DeepSeek response parse error: %s", exc)
            return self._fallback(request)

        results: list[ProductRecommendation] = []
        for rank, item in enumerate(items[:_MAX_RESULTS], start=1):
            marketplace = str(item.get("marketplace", "ozon")).lower()
            product_name = str(item.get("product_name", ""))
            try:
                price_rub = int(item.get("price_rub", 0))
            except (TypeError, ValueError):
                price_rub = 0

            if not product_name or price_rub <= 0 or price_rub > request.budget_rub:
                continue

            results.append(
                ProductRecommendation(
                    rank=rank,
                    product_name=product_name,
                    category=request.category,
                    season=request.season,
                    price_rub=price_rub,
                    marketplace=marketplace,
                    affiliate_url=_build_affiliate_url(
                        marketplace, product_name, self._partner_id
                    ),
                    image_url=None,
                    is_partner=False,  # set by RecommendationService
                    source="deepseek",
                )
            )

        if not results:
            return self._fallback(request)
        return results

    def _fallback(self, request: RecommendRequest) -> list[ProductRecommendation]:
        self._logger.info("DeepSeek: falling back to stub provider")
        from app.adapters.stub_product_search import StubProductSearchProvider

        return StubProductSearchProvider().search(request)
