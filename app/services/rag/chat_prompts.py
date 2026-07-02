"""
Промпты для AI-диалога.
AI сам решает, когда что уточнять, на основе ответов пользователя.
"""
import logging
from typing import Optional
from app.services.rag.knowledge_base import KnowledgeBase

# Экземпляр базы знаний (ленивая загрузка)
_kb = KnowledgeBase()
from app.services.rag.knowledge_base import KnowledgeBase

# Экземпляр базы знаний (ленивая загрузка)
_kb = KnowledgeBase()
from app.domain.models import TireRequest, TirePreferences, UserLocation

logger = logging.getLogger(__name__)

# Системный промпт для чата
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


def should_ask_for_wheels(request: TireRequest, user_message: str) -> bool:
    """Нужно ли спросить про диски."""
    keywords = ["диск", "колёса", "колесо", "катки", "штамповк", "литьё", "литой"]
    msg = user_message.lower()
    for kw in keywords:
        if kw in msg:
            return True
    # Если шины уже выбраны и не упомянуты диски
    if request and request.preferences.product_type.value == "tires":
        return True
    return False


def should_ask_for_bolts(request: TireRequest) -> bool:
    """Нужно ли спросить про крепёж."""
    return request.preferences.product_type in ("wheels", "assembly")


def should_ask_region(request: TireRequest) -> bool:
    """Спросить регион, если ещё не указан."""
    return request.location.region == "Москва" and request.location.city == "Москва"


def should_ask_delivery(request: TireRequest) -> bool:
    """Спросить про срочность."""
    return request.preferences.delivery_speed.value == "any"


def build_summary(request: TireRequest) -> str:
    """Сформировать сводку перед запуском подбора, обогащённую базой знаний."""
    lines = [
        "📋 **Сводка заказа**",
        f"🚗 Авто: {request.brand} {request.model} ({request.year})",
        f"📍 Регион: {request.location.region}, {request.location.city}",
        f"🏎️ Стиль: {request.driving_style.value}",
    ]
    if request.season:
        lines.append(f"🌤️ Сезон: {request.season.value}")
    if request.preferences.product_type:
        lines.append(f"🔧 Ищем: {request.preferences.product_type.value}")
    size = request.preferences.size_str()
    if size:
        lines.append(f"📐 Размер: {size}")
    if request.budget:
        lines.append(f"💰 Бюджет: до {request.budget} ₽")
    lines.append(f"📦 Доставка: {request.preferences.delivery_speed.value}")
    
    # Данные из базы знаний
    kb_data = _kb.enhance_prompt(
        brand=request.brand,
        model=request.model,
        year=request.year,
        tire_size=request.preferences.size_str(),
    )
    if kb_data:
        lines.append(f"\n📚 **Из базы знаний**")
        lines.append(kb_data)
    
    lines.append(f"\n✅ Запускаю подбор...")
    return "\n".join(lines)
