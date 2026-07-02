"""
База знаний для обогащения AI-рекомендаций.
Хранит отзывы, проверенные комбинации шин/авто, цены и проблемы.

Данные могут поступать из:
1. Парсинга форумов (Drive2, Pnevo, forums)
2. Ручного добавления
3. AI-анализа отзывов
"""
import json
import logging
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "knowledge")


@dataclass
class TireReview:
    """Отзыв владельца о шинах."""
    id: str
    car_brand: str
    car_model: str
    car_year: int
    tire_name: str
    tire_size: str
    rating: float
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    source: str = "forum"
    text: str = ""


@dataclass
class CarCompatibility:
    """Проверенные размеры шин и дисков для авто."""
    brand: str
    model: str
    min_year: int
    max_year: int
    tire_sizes: List[str] = field(default_factory=list)
    wheel_pcd: str = ""
    wheel_et: str = ""
    wheel_dia: str = ""
    bolt_thread: str = ""
    popular_tires: List[str] = field(default_factory=list)


@dataclass
class TireProblem:
    """Частые проблемы с конкретными шинами."""
    tire_name: str
    car_brand: str
    car_model: str
    problem: str
    severity: str = "info"  # "warning" | "critical"
    source: str = ""


class KnowledgeBase:
    """
    Поиск по базе знаний.
    Если файлы отсутствуют — возвращает пустоту (AI использует свои знания).
    """

    def __init__(self):
        self._reviews: Dict[str, List[TireReview]] = {}  # ключ: "brand_model"
        self._compatibility: Dict[str, CarCompatibility] = {}
        self._problems: Dict[str, List[TireProblem]] = {}
        self._loaded = False

    def load(self):
        """Загружает все JSON файлы из data/knowledge/."""
        if self._loaded:
            return
        
        self._load_json("reviews", self._parse_reviews)
        self._load_json("compatibility", self._parse_compatibility)
        self._load_json("problems", self._parse_problems)
        self._loaded = True
        logger.info("Knowledge base loaded: %d reviews, %d compat, %d problems",
                     len(self._reviews), len(self._compatibility), len(self._problems))

    def _load_json(self, folder: str, parser):
        path = os.path.join(BASE_DIR, folder)
        if not os.path.exists(path):
            return
        for fname in os.listdir(path):
            if fname.endswith(".json"):
                fpath = os.path.join(path, fname)
                try:
                    with open(fpath) as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            parser(item)
                    elif isinstance(data, dict):
                        parser(data)
                except Exception as e:
                    logger.warning("Error loading %s: %s", fpath, e)

    def _parse_reviews(self, item: dict):
        review = TireReview(**item)
        key = f"{review.car_brand.lower()}_{review.car_model.lower()}"
        if key not in self._reviews:
            self._reviews[key] = []
        self._reviews[key].append(review)

    def _parse_compatibility(self, item: dict):
        comp = CarCompatibility(**item)
        key = f"{comp.brand.lower()}_{comp.model.lower()}"
        self._compatibility[key] = comp

    def _parse_problems(self, item: dict):
        problem = TireProblem(**item)
        key = f"{problem.car_brand.lower()}_{problem.car_model.lower()}"
        if key not in self._problems:
            self._problems[key] = []
        self._problems[key].append(problem)

    def get_reviews(self, brand: str, model: str, tire_name: Optional[str] = None) -> List[TireReview]:
        """Получить отзывы для авто (и опционально для конкретных шин)."""
        self.load()
        key = f"{brand.lower()}_{model.lower()}"
        reviews = self._reviews.get(key, [])
        if tire_name:
            reviews = [r for r in reviews if tire_name.lower() in r.tire_name.lower()]
        return reviews

    def get_compatibility(self, brand: str, model: str, year: int) -> Optional[CarCompatibility]:
        """Получить совместимость для модели авто."""
        self.load()
        key = f"{brand.lower()}_{model.lower()}"
        comp = self._compatibility.get(key)
        if comp and comp.min_year <= year <= comp.max_year:
            return comp
        return None

    def get_problems(self, brand: str, model: str, tire_name: Optional[str] = None) -> List[TireProblem]:
        """Получить известные проблемы."""
        self.load()
        key = f"{brand.lower()}_{model.lower()}"
        problems = self._problems.get(key, [])
        if tire_name:
            problems = [p for p in problems if tire_name.lower() in p.tire_name.lower()]
        return problems

    def get_tire_sizes(self, brand: str, model: str, year: int) -> List[str]:
        """Получить рекомендуемые размеры шин для авто."""
        comp = self.get_compatibility(brand, model, year)
        return comp.tire_sizes if comp else []

    def get_popular_tires(self, brand: str, model: str, year: int) -> List[str]:
        """Какие шины чаще всего ставят на эту модель."""
        comp = self.get_compatibility(brand, model, year)
        return comp.popular_tires if comp else []

    def enhance_prompt(self, brand: str, model: str, year: int, tire_size: Optional[str] = None) -> str:
        """
        Обогащает промпт данными из базы знаний:
        - проверенные размеры
        - популярные шины
        - отзывы и проблемы
        """
        self.load()
        parts = []

        # Размеры
        sizes = self.get_tire_sizes(brand, model, year)
        if sizes:
            parts.append(f"Проверенные размеры шин для {brand} {model}: {', '.join(sizes)}.")

        # Популярные шины
        popular = self.get_popular_tires(brand, model, year)
        if popular:
            parts.append(f"Владельцы чаще всего ставят: {', '.join(popular)}.")

        # Отзывы для указанного размера
        if tire_size:
            tire_name = tire_size.split(" ")[0]  # берём первое слово
            reviews = self.get_reviews(brand, model, tire_name)[:3]
            if reviews:
                parts.append("Отзывы владельцев:")
                for r in reviews:
                    pros = ", ".join(r.pros[:3]) if r.pros else "нет данных"
                    cons = ", ".join(r.cons[:2]) if r.cons else "нет данных"
                    parts.append(f"- {r.tire_name}: +{pros}, -{cons}")

        # Проблемы
        problems = self.get_problems(brand, model)
        if problems:
            parts.append("Известные проблемы:")
            for p in problems[:3]:
                parts.append(f"⚠️ {p.tire_name}: {p.problem}")

        return "\n".join(parts)
