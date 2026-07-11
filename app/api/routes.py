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
from app.services.product_comparison import ProductComparisonService
from app.services.user_history import UserHistoryService, run_migration
from app.services.transliteration import normalize_brand, normalize_model
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


def _comparison_service() -> ProductComparisonService:
    """Получить сервис сравнения товаров."""
    if "product_comparison" not in current_app.extensions.get("services", {}):
        llm = current_app.extensions["services"].get("llm_client")
        if llm:
            current_app.extensions["services"]["product_comparison"] = ProductComparisonService(llm)
        else:
            raise RuntimeError("llm_client not initialized")
    return current_app.extensions["services"]["product_comparison"]


def _user_history_service() -> UserHistoryService:
    """Получить сервис истории пользователя."""
    if "user_history" not in current_app.extensions.get("services", {}):
        current_app.extensions["services"]["user_history"] = UserHistoryService()
    return current_app.extensions["services"]["user_history"]


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
        data['brand'] = normalize_brand(data['brand'])
        data['model'] = normalize_model(data['model'])

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

    user_id = data.get("user_id")

    async def _get_recommendation():
        # Проверяем кэш (без учёта user_id — общий кэш)
        cache = _cache()
        cache_key = f"recommend:{data['brand']}:{data['model']}:{data['year']}:{data['driving_style']}"
        cached = await cache.get_json(cache_key)
        if cached and not user_id:
            logger.info("Cache HIT for recommend_tires: %s", cache_key)
            return cached

        # Если есть user_id — добавляем историю в запрос к AI
        history_prompt = ""
        if user_id:
            try:
                history_prompt = await _user_history_service().build_history_prompt(user_id)
                if history_prompt:
                    logger.info("История пользователя %s добавлена к промпту", user_id)
            except Exception:
                logger.debug("Не удалось загрузить историю для %s", user_id)

        try:
            result = await _tire_service().get_recommendation(tire_request, history_prompt)
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
        if not user_id:
            await cache.set_json(cache_key, response, ttl=settings.CACHE_TTL_RECOMMEND)

        # Сохраняем запрос в историю пользователя
        if user_id:
            try:
                await _user_history_service().update_query(
                    user_id=user_id,
                    brand=data['brand'],
                    model=data['model'],
                    driving_style=data['driving_style'],
                    season=data.get('season'),
                    budget=data.get('budget'),
                )
            except Exception:
                logger.debug("Не удалось сохранить историю для %s", user_id)

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
    brand = normalize_brand(request.args.get('brand', ''))
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
#  AI Chat (умный диалог)
# ──────────────────────────────────────────────

@api_blueprint.route('/chat', methods=['POST'])
def ai_chat():
    """
    Умный AI-чат. Принимает историю сообщений и текущие данные пользователя.
    DeepSeek ведёт диалог, задаёт уточняющие вопросы, помогает подобрать шины.

    Body: {
        "messages": [{"role": "user", "content": "У меня Тойота Камри"}, ...],
        "user_data": {"brand": null, "model": null, ...},  // текущее состояние
        "user_id": "optional"
    }
    Returns: {
        "reply": "ответ AI",
        "user_data": {"brand": "Toyota", "model": "Camry", ...},  // обновлённое
        "ready": false,  // true если все данные собраны
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    messages = data.get("messages", [])
    user_data = data.get("user_data", {})
    user_id = data.get("user_id")

    if not messages:
        return jsonify({"error": "Missing messages"}), 400

    async def _get_ai_response():
        llm = current_app.extensions["services"].get("llm_client")

        # Формируем системный промпт с текущим состоянием
        filled_fields = []
        if user_data.get("brand"): filled_fields.append(f"Марка: {user_data['brand']}")
        if user_data.get("model"): filled_fields.append(f"Модель: {user_data['model']}")
        if user_data.get("year"): filled_fields.append(f"Год: {user_data['year']}")
        if user_data.get("driving_style"): filled_fields.append(f"Стиль: {user_data['driving_style']}")
        if user_data.get("season"): filled_fields.append(f"Сезон: {user_data['season']}")
        if user_data.get("budget"): filled_fields.append(f"Бюджет: {user_data['budget']}₽")

        filled_str = "Известно:\n" + "\n".join(filled_fields) if filled_fields else "Данных пока нет."
        missing = []
        if not user_data.get("brand"): missing.append("марка")
        if not user_data.get("model"): missing.append("модель")
        if not user_data.get("year"): missing.append("год")
        if not user_data.get("driving_style"): missing.append("стиль вождения")
        if not user_data.get("season"): missing.append("сезон")
        missing_str = f"Нужно узнать: {', '.join(missing)}." if missing else "Все данные собраны!"

        # История пользователя, если есть
        history_prompt = ""
        if user_id:
            try:
                history_prompt = await _user_history_service().build_history_prompt(user_id)
            except Exception:
                pass

        system_prompt = (
            "Ты — AI-консультант по подбору автомобильных шин в чате. "
            "Твоя задача — собирать данные от пользователя в разговоре и рекомендовать шины.\n\n"
            f"{filled_str}\n{missing_str}\n\n"
            f"{'История пользователя: ' + history_prompt if history_prompt else ''}"
            "\n\nПравила:\n"
            "1. Отвечай коротко и дружелюбно, задавай следующие вопросы по очереди\n"
            "2. Если пользователь назвал что-то на русском — используй латинские названия\n"
            "3. Извлекай из ответов пользователя: марку, модель, год, стиль вождения, сезон, бюджет\n"
            "4. Если все данные собраны — скажи что готов и напиши 'ГОТОВ_К_ПОДБОРУ'\n"
            "5. Не придумывай данные за пользователя — спрашивай если не уверен\n"
            "6. Отвечай НА ТОМ ЖЕ ЯЗЫКЕ что и пользователь"
        )

        # Преобразуем сообщения в формат DeepSeek
        deepseek_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages[-10:]:  # последние 10 сообщений (контекст)
            role = msg.get("role", "user")
            deepseek_messages.append({"role": role, "content": msg.get("content", "")})

        try:
            reply = await llm.generate_text(
                prompt="",  # messages уже есть в deepseek_messages
                system_prompt="",  # будет проигнорирован, используем chat-style
                messages=deepseek_messages,
            )
        except TypeError:
            # Fallback: если generate_text не поддерживает messages
            last_user_msg = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
            )
            prompt = f"{system_prompt}\n\nПоследнее сообщение пользователя: {last_user_msg}"
            reply = await llm.generate_text(prompt, system_prompt="Ты — эксперт по шинам.")

        # Проверяем готовность
        ready = "ГОТОВ_К_ПОДБОРУ" in reply

        # Парсим user_data из ответа (если AI упомянул новые данные)
        parsed = _parse_ai_reply(reply, user_data)

        return {
            "reply": reply.replace("ГОТОВ_К_ПОДБОРУ", "").strip(),
            "user_data": parsed,
            "ready": ready,
        }

    response = _run_async(_get_ai_response())
    return jsonify(response), 200


def _parse_ai_reply(reply: str, current_user_data: dict) -> dict:
    """Пытается извлечь данные из ответа AI (дополнительно к фронтенд-парсингу)."""
    import re
    result = dict(current_user_data)

    # Ищем паттерны
    patterns = {
        "brand": r"марка[:\s]*([А-Яа-яA-Za-z-]+)",
        "model": r"модель[:\s]*([А-Яа-яA-Za-z0-9-]+)",
        "year": r"(\d{4})\s*(год|г\.|году)",
        "budget": r"бюджет[:\s]*(\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, reply.lower())
        if match:
            val = match.group(1).strip()
            if key == "brand":
                from app.services.transliteration import normalize_brand
                val = normalize_brand(val)
            elif key == "model":
                from app.services.transliteration import normalize_model
                val = normalize_model(val)
            if val and not result.get(key):
                result[key] = val

    return result

@api_blueprint.route('/compare_tires', methods=['POST'])
def compare_tires():
    """Сравнение 2–4 товаров. Возвращает таблицу сравнения + рекомендацию AI."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    products_data = data.get("products", [])
    if len(products_data) < 2:
        return jsonify({"error": "Need at least 2 products to compare"}), 400
    if len(products_data) > 4:
        return jsonify({"error": "Maximum 4 products for comparison"}), 400

    # Преобразуем в Product
    from app.domain.models import Product as ProductModel
    products = []
    for p in products_data:
        products.append(ProductModel(
            id=p.get("id", ""),
            name=p.get("name", "Unknown"),
            price=float(p.get("price", 0)),
            currency=p.get("currency", "₽"),
            rating=float(p.get("rating", 0)) if p.get("rating") else None,
            image_url=p.get("image_url", ""),
            partner_link=p.get("partner_link", ""),
            source=p.get("source", ""),
        ))

    async def _get_comparison():
        try:
            result = await _comparison_service().compare(products)
            return {
                "products": [
                    {
                        "name": item.name,
                        "price": item.price,
                        "rating": item.rating,
                        "pros": item.pros,
                        "cons": item.cons,
                        "best_for": item.best_for,
                    }
                    for item in result.products
                ],
                "summary": result.summary,
                "advice": result.raw_advice,
            }
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.exception("Comparison failed")
            return {"error": "Internal server error"}

    response = _run_async(_get_comparison())
    status = 200 if "error" not in response or not response.get("products") else 400
    return jsonify(response), status


# ──────────────────────────────────────────────
#  User history (персонализация)
# ──────────────────────────────────────────────

@api_blueprint.route('/user/history', methods=['POST'])
def user_history():
    """Сохранить / получить историю пользователя."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    async def _handle_history():
        service = _user_history_service()

        # Если это запрос истории
        if data.get("action") == "get":
            prompt_part = await service.build_history_prompt(user_id)
            profile = await service.get_profile(user_id)
            return {
                "history_prompt": prompt_part,
                "profile": {
                    "total_queries": profile.total_queries,
                    "preferred_brand": profile.preferred_brand,
                    "preferred_model": profile.preferred_model,
                    "preferred_driving_style": profile.preferred_driving_style,
                    "preferred_season": profile.preferred_season,
                    "preferred_budget": profile.preferred_budget,
                    "purchased_tires": profile.purchased_tires,
                },
            }

        # Если это запись нового запроса
        elif data.get("action") == "save_query":
            await service.update_query(
                user_id=user_id,
                brand=data.get("brand", ""),
                model=data.get("model", ""),
                driving_style=data.get("driving_style", "comfort"),
                season=data.get("season"),
                budget=data.get("budget"),
            )
            return {"status": "ok", "message": "History updated"}

        # Если это запись покупки
        elif data.get("action") == "save_purchase":
            tire_name = data.get("tire_name")
            if tire_name:
                await service.add_purchase(user_id, tire_name)
                return {"status": "ok", "message": f"Purchase saved: {tire_name}"}
            return {"error": "Missing tire_name"}, 400

        return {"error": "Unknown action"}, 400

    response = _run_async(_handle_history())
    status = 200 if "error" not in response else 400
    return jsonify(response), status


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
