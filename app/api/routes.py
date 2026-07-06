from __future__ import annotations

import asyncio
import logging

from flask import Blueprint, current_app, jsonify, request

from app.adapters.deepseek_client import DeepSeekClient
from app.adapters.partner_api import MockPartnerCatalog
from app.api.errors import ApiError
from app.domain.models import TireRequest, DrivingStyle, Season
from app.services.part_recognition import PartRecognitionService
from app.services.tire_recomendation import TireRecommendationService
from app.services.vin_decoder import VinDecoderService
from app.services.cache import get_cache
from app.config.settings import settings


logger = logging.getLogger(__name__)

api_blueprint = Blueprint("api", __name__, url_prefix="/api")


@api_blueprint.route('/health', methods=['GET'])
def health():
    """Healthcheck для Docker."""
    return jsonify({"status": "ok", "service": "avto-expert-ai"}), 200


def _part_service() -> PartRecognitionService:
    return current_app.extensions["services"]["part_recognition"]


def _vin_service() -> VinDecoderService:
    return current_app.extensions["services"]["vin_decoder"]


def _tire_service() -> TireRecommendationService:
    return current_app.extensions["services"]["tire_recommendation"]


def _cache():
    """Получить сервис кэша."""
    return get_cache()


def _run_async(coro):
    """Запустить асинхронную корутину в синхронном контексте Flask."""
    return asyncio.run(coro)


# ──────────────────────────────────────────────
#  Recognise part
# ──────────────────────────────────────────────

@api_blueprint.post("/recognize-part")
def recognize_part():
    if request.mimetype and request.mimetype.startswith("multipart/form-data"):
        upload = request.files.get("image")
        if upload is None:
            raise ApiError(
                code="missing_image_payload",
                message="Multipart requests must include an 'image' file field.",
                status_code=400,
            )

        result = _part_service().recognize_upload(
            upload.read(),
            declared_mime_type=upload.mimetype,
            filename=upload.filename,
        )
        return jsonify(result.to_dict()), 200

    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ApiError(
                code="invalid_json",
                message="Request body must contain valid JSON.",
                status_code=400,
            )

        result = _part_service().recognize_base64(
            payload.get("image_base64"),
            declared_mime_type=payload.get("content_type"),
            filename=payload.get("filename"),
        )
        return jsonify(result.to_dict()), 200

    raise ApiError(
        code="unsupported_media_type",
        message="Use multipart/form-data or application/json for this endpoint.",
        status_code=415,
        details={"allowed_content_types": ["multipart/form-data", "application/json"]},
    )


# ──────────────────────────────────────────────
#  Decode VIN
# ──────────────────────────────────────────────

@api_blueprint.route("/decode-vin", methods=["GET", "POST"])
def decode_vin():
    vin_value = request.args.get("vin", "")
    if request.method == "POST" and request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise ApiError(
                code="invalid_json",
                message="Request body must contain valid JSON.",
                status_code=400,
            )
        vin_value = payload.get("vin", vin_value)

    if not vin_value:
        raise ApiError(
            code="missing_vin",
            message="VIN is required in the query string or JSON body.",
            status_code=400,
        )

    result = _vin_service().decode(vin_value)
    return jsonify(result.to_dict()), 200 if result.is_valid else 422


# ──────────────────────────────────────────────
#  Tire recommendation (Mini App endpoints)
# ──────────────────────────────────────────────

@api_blueprint.route('/recommend_tires', methods=['POST'])
def recommend_tires():
    """Эндпоинт для Mini App: принимает JSON с параметрами, возвращает рекомендации."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required = ['brand', 'model', 'year', 'driving_style']
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing fields: {required}"}), 400

    try:
        tire_request = TireRequest(
            brand=data['brand'],
            model=data['model'],
            year=int(data['year']),
            driving_style=DrivingStyle(data['driving_style']),
            budget=int(data['budget']) if data.get('budget') else None,
            season=Season(data['season']) if data.get('season') else None,
        )
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400

    async def _get_recommendation():
        # Проверяем кэш
        cache = _cache()
        cache_key = f"recommend:{data['brand']}:{data['model']}:{data['year']}:{data['driving_style']}"
        cached = await cache.get_json(cache_key)
        if cached:
            logger.info("Cache HIT for recommend_tires: %s", cache_key)
            return cached

        try:
            result = await _tire_service().get_recommendation(tire_request)
        except Exception:
            logger.exception("Recommendation failed")
            return None

        response = {
            "advice": result.advice,
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "currency": p.currency,
                    "image_url": p.image_url,
                    "partner_link": p.partner_link,
                    "source": p.source,
                } for p in result.products
            ],
            "request": {
                "brand": result.request.brand,
                "model": result.request.model,
                "year": result.request.year,
                "driving_style": result.request.driving_style.value,
                "budget": result.request.budget,
                "season": result.request.season.value if result.request.season else None,
            },
        }

        # Сохраняем в кэш на 10 минут
        await cache.set_json(cache_key, response, ttl=settings.CACHE_TTL_RECOMMEND)

        return response

    response = _run_async(_get_recommendation())

    if response is None:
        return jsonify({"error": "Internal server error"}), 500

    return jsonify(response), 200


# ──────────────────────────────────────────────
#  Brands & Models (с кэшированием)
# ──────────────────────────────────────────────

@api_blueprint.route('/brands', methods=['GET'])
def get_brands():
    """Возвращает список популярных марок с кэшированием."""
    cache = _cache()
    cache_key = "brands:list"

    # Пробуем из кэша (синхронная обёртка)
    async def _get_cached():
        return await cache.get_json(cache_key)

    cached = _run_async(_get_cached())
    if cached:
        return jsonify(cached), 200

    brands = [
        "Lada", "Kia", "Hyundai", "Toyota", "Volkswagen",
        "Skoda", "Nissan", "Mitsubishi", "BMW", "Mercedes-Benz",
        "Audi", "Ford", "Renault", "Chevrolet", "Mazda",
    ]
    brands_sorted = sorted(brands)

    # Кэшируем на 1 час
    async def _set_cache():
        await cache.set_json(cache_key, brands_sorted, ttl=settings.CACHE_TTL_BRANDS)

    _run_async(_set_cache())

    return jsonify(brands_sorted), 200


@api_blueprint.route('/models', methods=['GET'])
def get_models():
    """Возвращает модели для выбранной марки (с кэшированием)."""
    brand = request.args.get('brand')
    if not brand:
        return jsonify({"error": "Missing brand parameter"}), 400

    cache = _cache()
    cache_key = f"models:{brand.lower()}"

    async def _get_cached():
        return await cache.get_json(cache_key)

    cached = _run_async(_get_cached())
    if cached:
        return jsonify(cached), 200

    mock_models = {
        "Toyota": ["Camry", "Corolla", "RAV4", "Land Cruiser", "Yaris"],
        "Kia": ["Rio", "Sportage", "Cerato", "Stinger", "Soul"],
        "Hyundai": ["Solaris", "Creta", "Tucson", "Elantra", "Santa Fe"],
        "Lada": ["Granta", "Vesta", "Niva", "Kalina", "Priora"],
        "Volkswagen": ["Polo", "Golf", "Passat", "Tiguan", "Jetta"],
    }
    models = mock_models.get(brand, [])

    async def _set_cache():
        await cache.set_json(cache_key, models, ttl=settings.CACHE_TTL_MODELS)

    _run_async(_set_cache())

    return jsonify(models), 200


# ──────────────────────────────────────────────
#  Lang files
# ──────────────────────────────────────────────

@api_blueprint.route('/lang/<lang_code>', methods=['GET'])
def get_lang(lang_code):
    """Возвращает JSON-файл локализации."""
    import json, os
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lang_path = os.path.join(base, 'miniapp', 'static', 'lang', f'{lang_code}.json')
    if not os.path.exists(lang_path):
        lang_path = os.path.join(base, 'miniapp', 'static', 'lang', 'ru.json')
    try:
        with open(lang_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
