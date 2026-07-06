"""Доменные модели проекта GarageMind AI."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TireCategory(Enum):
    """Категория шин по назначению."""
    standard = "standard"              # стандартные (город, трасса)
    sport = "sport"                   # спортивные (высокая скорость, управляемость)
    comfort = "comfort"               # комфортные (тихие, мягкие)
    off_road = "off_road"             # внедорожные (грязь, бездорожье)
    winter_studded = "winter_studded" # зимние шипованные
    winter_friction = "winter_friction" # зимние нешипованные (липучка)
    all_season = "all_season"         # всесезонные
    economical = "economical"         # экономичные (низкое сопротивление качению)
    run_flat = "run_flat"             # RunFlat (можно ехать на спущенной)
    heavy_load = "heavy_load"         # усиленные (для тяжёлых авто)


class TireFeature(Enum):
    """Дополнительные свойства шин."""
    reinforced = "reinforced"          # усиленная боковина (XL / Extra Load)
    low_profile = "low_profile"        # низкий профиль
    high_profile = "high_profile"      # высокий профиль
    directional = "directional"        # направленный рисунок
    asymmetric = "asymmetric"          # асимметричный рисунок
    silent = "silent"                  # тихая (с шумоподавлением)
    studdable = "studdable"            # можно ошиповать
    tubeless = "tubeless"              # бескамерная
    ev_compatible = "ev_compatible"    # для электромобилей
    of_road_mud = "of_road_mud"        # грязевые (M/T)
    of_road_all = "of_road_all"        # универсальные (A/T)


class DrivingStyle(Enum):
    comfort = "comfort"
    sport = "sport"
    economy = "economy"


class Season(Enum):
    summer = "summer"
    winter = "winter"
    all_season = "all_season"


class DeliverySpeed(Enum):
    """Важность срока доставки."""
    any = "any"                # не важно
    within_3_days = "3days"    # в течение 3 дней
    within_week = "week"       # в течение недели
    urgent = "urgent"          # срочно (1-2 дня)


class OrderType(Enum):
    """Способ получения."""
    pickup = "pickup"          # самовывоз
    delivery = "delivery"      # доставка


class PaymentMethod(Enum):
    cash = "cash"
    card = "card"
    online = "online"
    installments = "installments"


@dataclass
class UserLocation:
    """Регион пользователя."""
    region: str                # регион: "Москва", "Краснодарский край"
    city: str                  # город: "Москва", "Сочи"
    delivery_city: Optional[str] = None  # город доставки (если отличается)
    search_scope: str = "region"  # "region" | "all" — искать в регионе или везде

    def __post_init__(self):
        if not self.delivery_city:
            self.delivery_city = self.city


@dataclass
class TirePreferences:
    """
    Расширенные предпочтения пользователя по шинам.
    
    Добавляет к базовому запросу:
    - регион (влияет на цены и доступность)
    - срок доставки
    - способ получения
    - размер шин
    - бренды шин
    - гарантия
    """
    # Размеры шин (опционально, если пользователь знает)
    tire_width: Optional[int] = None          # 205
    tire_profile: Optional[int] = None        # 55
    tire_diameter: Optional[int] = None       # 16
    
    # Доставка
    delivery_speed: DeliverySpeed = DeliverySpeed.any
    order_type: OrderType = OrderType.delivery
    
    # Оплата
    payment_method: PaymentMethod = PaymentMethod.card
    
    # Поиск
    preferred_brands: List[str] = field(default_factory=list)  # Michelin, Bridgestone...
    tire_category: Optional[TireCategory] = None  # категория шин
    tire_features: List[TireFeature] = field(default_factory=list)  # доп свойства
    exclude_brands: List[str] = field(default_factory=list)    # Nokian...
    only_in_stock: bool = True               # только в наличии
    min_rating: Optional[float] = None       # минимальный рейтинг
    min_warranty_months: Optional[int] = None  # минимальная гарантия

    def size_str(self) -> Optional[str]:
        """Вернуть строку размера, если все поля заданы: '205/55 R16'."""
        if self.tire_width and self.tire_profile and self.tire_diameter:
            return f"{self.tire_width}/{self.tire_profile} R{self.tire_diameter}"
        return None


@dataclass
class TireRequest:
    """Полный запрос пользователя на подбор шин."""
    # Основные параметры
    brand: str
    model: str
    year: int
    driving_style: DrivingStyle
    season: Optional[Season] = None
    budget: Optional[int] = None
    
    # Расширенные параметры
    preferences: TirePreferences = field(default_factory=TirePreferences)
    location: UserLocation = field(
        default_factory=lambda: UserLocation(region="Москва", city="Москва")
    )

    def to_dict(self) -> dict:
        """Сериализация для API и логирования."""
        d = {
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "driving_style": self.driving_style.value,
        }
        if self.season:
            d["season"] = self.season.value
        if self.budget:
            d["budget"] = self.budget
        
        # Расширенные параметры
        d["region"] = self.location.region
        d["city"] = self.location.city
        d["delivery_city"] = self.location.delivery_city
        d["delivery_speed"] = self.preferences.delivery_speed.value
        d["order_type"] = self.preferences.order_type.value
        d["only_in_stock"] = self.preferences.only_in_stock
        
        size = self.preferences.size_str()
        if size:
            d["tire_size"] = size
            
        return d


@dataclass
class Product:
    """Товар (шина) с полной информацией."""
    id: str
    name: str
    price: float
    currency: str = "RUB"
    image_url: Optional[str] = None
    partner_link: Optional[str] = None
    source: Optional[str] = None
    rating: Optional[float] = None
    
    # Новая информация
    in_stock: bool = True
    stock_count: Optional[int] = None
    delivery_days: Optional[int] = None       # дней до доставки
    delivery_price: Optional[float] = None    # стоимость доставки
    pickup_available: bool = False
    warranty_months: Optional[int] = None
    payment_methods: List[PaymentMethod] = field(default_factory=list)
    
    # Размер
    tire_width: Optional[int] = None
    tire_profile: Optional[int] = None
    tire_diameter: Optional[int] = None


@dataclass
class RecommendationResult:
    """Результат рекомендации."""
    advice: str
    products: List[Product]
    request: TireRequest
    popular_pick: Optional[Product] = None
    warnings: List[str] = field(default_factory=list)  # "шины дороже бюджета", "доставка 5 дней"


# ============================================================
# VIN Decoder models
# ============================================================

@dataclass
class VinDecoded:
    """Расшифрованный VIN-номер."""
    wmi: Optional[str] = None                  # World Manufacturer Identifier
    region: Optional[str] = None               # Регион производства
    manufacturer: Optional[str] = None          # Производитель
    model_year: Optional[int] = None            # Год выпуска
    plant_code: Optional[str] = None            # Код завода
    serial: Optional[str] = None                # Серийный номер


@dataclass
class VinDecodeResult:
    """Результат декодирования VIN."""
    vin: str
    is_valid: bool
    validation_errors: List[str]
    decoded: VinDecoded
