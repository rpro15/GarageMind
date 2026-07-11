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


# Словарь популярных моделей (кириллица → латиница)
_MODEL_MAP = {
    # Toyota
    "камри": "Camry",
    "королла": "Corolla",
    "рав 4": "RAV4",
    "рав4": "RAV4",
    "лэнд крузер": "Land Cruiser",
    "лэнд крузер 300": "Land Cruiser 300",
    "прадо": "Land Cruiser Prado",
    "хайлендер": "Highlander",
    "хиллюкс": "Hilux",
    "хайс": "Hiace",
    "альфард": "Alphard",
    "супра": "Supra",
    "ярис": "Yaris",
    "снр": "C-HR",
    # BMW
    "х3": "X3",
    "х5": "X5",
    "х1": "X1",
    "х7": "X7",
    "3 серия": "3 Series",
    "5 серия": "5 Series",
    "7 серия": "7 Series",
    # Mercedes
    "е класс": "E-Class",
    "с класс": "C-Class",
    "glc": "GLC",
    "gle": "GLE",
    "глк": "GLC",
    "glа": "GLA",
    "gls": "GLS",
    "v класс": "V-Class",
    "s класс": "S-Class",
    # Audi
    "q5": "Q5",
    "q7": "Q7",
    "а6": "A6",
    "а4": "A4",
    "q3": "Q3",
    "а8": "A8",
    "етрон": "e-tron",
    # Kia
    "рио": "Rio",
    "спортейдж": "Sportage",
    "серато": "Cerato",
    "стингер": "Stinger",
    "соул": "Soul",
    "селтос": "Seltos",
    "соренто": "Sorento",
    "пиканто": "Picanto",
    "карнивал": "Carnival",
    "к5": "K5",
    "ев6": "EV6",
    # Hyundai
    "солярис": "Solaris",
    "крета": "Creta",
    "туссан": "Tucson",
    "элантра": "Elantra",
    "санта фе": "Santa Fe",
    "соната": "Sonata",
    "палисад": "Palisade",
    "кона": "Kona",
    "айоник": "IONIQ",
    # Volkswagen
    "поло": "Polo",
    "гольф": "Golf",
    "пассат": "Passat",
    "тигуан": "Tiguan",
    "туарег": "Touareg",
    "джетта": "Jetta",
    "таос": "Taos",
    "террамонт": "Teramont",
    "id.4": "ID.4",
    # Skoda
    "октавия": "Octavia",
    "рапид": "Rapid",
    "кодиак": "Kodiaq",
    "карок": "Karoq",
    "суперб": "Superb",
    # Renault
    "логан": "Logan",
    "дастер": "Duster",
    "каптюр": "Kaptur",
    "аркана": "Arkana",
    "сандеро": "Sandero",
    # Nissan
    "кашкай": "Qashqai",
    "икс-трейл": "X-Trail",
    "террано": "Terrano",
    "альмера": "Almera",
    "жук": "Juke",
    # Lada
    "гранта": "Granta",
    "веста": "Vesta",
    "нива": "Niva Legend",
    "нива легенд": "Niva Legend",
    "нива тревел": "Niva Travel",
    "ларгус": "Largus",
    "калина": "Kalina",
    "приора": "Priora",
    "икс рей": "XRAY",
    "иксрей": "XRAY",
    # Mazda
    "сх-5": "CX-5",
    "сх5": "CX-5",
    "сх-9": "CX-9",
    "сх9": "CX-9",
    "сх-30": "CX-30",
    "сх30": "CX-30",
    "мазда 6": "Mazda 6",
    "мазда 3": "Mazda 3",
    # Ford
    "фокус": "Focus",
    "куга": "Kuga",
    "эксплорер": "Explorer",
    "транзит": "Transit",
    "мустанг": "Mustang",
    # Chery
    "тигго 4": "Tiggo 4",
    "тигго 7": "Tiggo 7 Pro",
    "тигго 8": "Tiggo 8 Pro",
    "тигго 8 про": "Tiggo 8 Pro",
    "тигго 9": "Tiggo 9",
    "аризо 8": "Arrizo 8",
    # Haval
    "джолион": "Jolion",
    "ф7": "F7",
    "ф7х": "F7x",
    "дарго": "Dargo",
    "х6": "H6",
    "х9": "H9",
    "м6": "M6 Plus",
    # Geely
    "монжаро": "Monjaro",
    "атлас про": "Atlas Pro",
    "кулрей": "Coolray",
    "тугелла": "Tugella",
    "окованго": "Okavango",
    # Changan
    "сэс 35": "CS35 Plus",
    "сэс 55": "CS55 Plus",
    "сэс 75": "CS75 Plus",
    "юник": "UNI-K",
    "уник": "UNI-K",
    # Mitsubishi
    "аутлендер": "Outlander",
    "паджеро": "Pajero Sport",
    "паджео спорт": "Pajero Sport",
    "л200": "L200",
    "асх": "ASX",
    "эклипс": "Eclipse Cross",
    # Suzuki
    "витара": "Vitara",
    "джимни": "Jimny",
    "свифт": "Swift",
}


def normalize_model(model: str) -> str:
    """Приводит модель к латинице — сначала из словаря, потом транслитерация."""
    cleaned = model.strip().lower()
    # 1. Прямое совпадение в словаре
    if cleaned in _MODEL_MAP:
        return _MODEL_MAP[cleaned]
    # 2. Поиск по частичному совпадению (для "королла 2020" -> "Corolla")
    for ru_name, en_name in _MODEL_MAP.items():
        if ru_name in cleaned or cleaned in ru_name:
            return en_name
    # 3. Проверяем, есть ли кириллица — транслитерируем
    if any('а' <= ch <= 'я' or ch == 'ё' for ch in cleaned):
        return transliterate(cleaned)
    return model.strip()
