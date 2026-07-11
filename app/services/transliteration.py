"""
Транслитерация кириллических названий брендов и моделей авто в латиницу.
"""
from __future__ import annotations

# Основной словарь кириллица → латиница
_CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
    'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'iu', 'я': 'ia',
}

# Известные бренды на русском → латиница (для точного соответствия)
_BRAND_MAP = {
    "тойота": "Toyota",
    "бмв": "BMW",
    "мерседес": "Mercedes-Benz",
    "мерседес-бенц": "Mercedes-Benz",
    "ауди": "Audi",
    "киа": "Kia",
    "kia": "Kia",
    "хёндэ": "Hyundai",
    "хендай": "Hyundai",
    "хендэ": "Hyundai",
    "лада": "Lada",
    "ваз": "Lada",
    "ниссан": "Nissan",
    "мазда": "Mazda",
    "форд": "Ford",
    "шевроле": "Chevrolet",
    "шкода": "Skoda",
    "фольксваген": "Volkswagen",
    "рено": "Renault",
    "митсубиси": "Mitsubishi",
    "мицубиси": "Mitsubishi",
    "лексус": "Lexus",
    "хонда": "Honda",
    "субару": "Subaru",
    "пежо": "Peugeot",
    "ситроен": "Citroen",
    "опель": "Opel",
    "вольво": "Volvo",
    "фиат": "Fiat",
    "генesis": "Genesis",
    "черри": "Chery",
    "хавал": "Haval",
    "джили": "Geely",
    "чанъань": "Changan",
    "changan": "Changan",
    "уаз": "UAZ",
    "газ": "GAZ",
    "москвич": "Moskvich",
    "порше": "Porsche",
    "ягуар": "Jaguar",
    "ленд ровер": "Land Rover",
    "land rover": "Land Rover",
    "landrover": "Land Rover",
    "tesla": "Tesla",
    "тесла": "Tesla",
}


def transliterate(text: str) -> str:
    """Простая транслитерация кириллицы в латиницу."""
    result = []
    for ch in text.lower():
        result.append(_CYRILLIC_TO_LATIN.get(ch, ch))
    return "".join(result)


def normalize_brand(brand: str) -> str:
    """Приводит название бренда к стандартной латинской форме."""
    cleaned = brand.strip()
    key = cleaned.lower().replace("-", " ").strip()
    if key in _BRAND_MAP:
        return _BRAND_MAP[key]
    # Если не нашли в словаре — пробуем транслитерацию
    translit = transliterate(cleaned)
    # Делаем первую букву заглавной
    return translit.capitalize() if translit else cleaned


def normalize_model(model: str) -> str:
    """Приводит модель к латинице через транслитерацию."""
    cleaned = model.strip()
    # Проверяем, есть ли кириллица
    if any('а' <= ch <= 'я' or ch == 'ё' for ch in cleaned.lower()):
        return transliterate(cleaned)
    return cleaned
