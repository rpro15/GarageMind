"""
Промпты для AI-диалога.
AI сам решает, когда что уточнять, на основе ответов пользователя.
"""
import logging
from typing import Optional

_LOGGER = logging.getLogger(__name__)

# Ленивый импорт для избежания side-эффектов при импорте модуля
_db = None
_kb = None


def _get_db():
    global _db
    if _db is None:
        from app.services.database import DatabaseService
        _db = DatabaseService()
    return _db


def _get_kb():
    global _kb
    if _kb is None:
        from app.services.rag.knowledge_base import KnowledgeBase
        _kb = KnowledgeBase()
    return _kb


CHAT_SYSTEM_PROMPT = """Ты — AI-консультант по подбору шин, дисков и крепежа в Telegram Mini App.

Твоя задача — собрать все данные для подбора. 
Уточняй шаг за шагом, задавай ТОЛЬКО 1 вопрос за раз.

Последовательность опроса (если пользователь сам что-то не сказал):
1️⃣ Марка и модель автомобиля
2️⃣ Год выпуска
3️⃣ Регион и город (влияет на цену и доставку)
4️⃣ Стиль вождения (комфорт/спорт/эконом)
5️⃣ Сезон (лето/зима/всесезон)
6️⃣ Что ищем: шины, диски, или колёса в сборе
7️⃣ Если диски — материал (штамповка/литьё)
8️⃣ Знает ли размер шин (ширина/профиль/диаметр)
   - Если знает → уточнить
   - Если нет → подобрать по автомобилю
9️⃣ Срочность доставки (срочно/в течение недели/неважно)
🔟 Бюджет (можно пропустить)

ВАЖНО:
- Не спрашивай всё сразу. Один вопрос — один ответ.
- Если пользователь сказал "не знаю" — предложи подобрать автоматически.
- После сбора всех данных скажи: "Собрал данные, запускаю подбор..."
- Будь дружелюбным, используй эмодзи 🚗
- Если пользователь хочет диски — уточни PCD, вылет, ЦО (или подбери по машине)"""


def should_ask_for_wheels(request, user_message: str) -> bool:
    """Нужно ли спросить про диски."""
    keywords = ["диск", "колёса", "колесо", "катки", "штамповк", "литьё", "литой"]
    msg = user_message.lower()
    for kw in keywords:
        if kw in msg:
            return True
    return False


def should_ask_for_bolts(request) -> bool:
    """Нужно ли спросить про крепёж."""
    pt = getattr(request, 'product_type', None) or getattr(getattr(request, 'preferences', None), 'product_type', None)
    return pt in ("wheels", "assembly") if pt else False


def should_ask_region(request) -> bool:
    """Спросить регион, если ещё не указан."""
    loc = getattr(request, 'location', None)
    if loc:
        return loc.region == "Москва" and loc.city == "Москва"
    return False


def should_ask_delivery(request) -> bool:
    """Спросить про срочность."""
    pref = getattr(request, 'preferences', None)
    if pref:
        return getattr(pref, 'delivery_speed', None) and pref.delivery_speed.value == "any"
    return False


def build_summary(request) -> str:
    """Сформировать сводку перед запуском подбора, обогащённую базой знаний."""
    lines = [
        "📋 **Сводка заказа**",
    ]

    # Безопасное получение атрибутов
    brand = getattr(request, 'brand', None)
    model = getattr(request, 'model', None)
    year = getattr(request, 'year', None)
    location = getattr(request, 'location', None)
    driving_style = getattr(request, 'driving_style', None)
    season = getattr(request, 'season', None)
    budget = getattr(request, 'budget', None)
    preferences = getattr(request, 'preferences', None)

    if brand and model and year:
        lines.append(f"🚗 Авто: {brand} {model} ({year})")
    if location:
        lines.append(f"📍 Регион: {location.region}, {location.city}")
    if driving_style:
        lines.append(f"🏎️ Стиль: {driving_style.value if hasattr(driving_style, 'value') else driving_style}")
    if season:
        lines.append(f"🌤️ Сезон: {season.value if hasattr(season, 'value') else season}")
    if budget:
        lines.append(f"💰 Бюджет: до {budget} ₽")

    # Доставка
    if preferences:
        ds = getattr(preferences, 'delivery_speed', None)
        if ds:
            lines.append(f"📦 Доставка: {ds.value if hasattr(ds, 'value') else ds}")

    # Данные из базы знаний
    if brand and model and year:
        try:
            kb_data = _get_kb().enhance_prompt(
                brand=brand,
                model=model,
                year=year,
            )
            if kb_data:
                lines.append(f"\n📚 **Из базы знаний**")
                lines.append(kb_data)
        except Exception:
            _LOGGER.debug("Knowledge base lookup failed", exc_info=True)

    lines.append(f"\n✅ Запускаю подбор...")
    return "\n".join(lines)
