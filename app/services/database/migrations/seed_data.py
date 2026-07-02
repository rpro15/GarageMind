"""Миграция: наполнение базы знаний начальными данными.
Запуск: python -m app.services.database.migrations.seed_data"""
import logging
from app.services.database.schema import DatabaseService, CarModel, TireReview, TireProblem, TireSpec

logger = logging.getLogger(__name__)


def seed():
    db = DatabaseService()

    # Если данные уже есть — не дублируем
    if db.car_count() > 0:
        logger.info(f"База уже содержит {db.car_count()} авто, seed пропущен.")
        return

    # ============================================================
    # CAR MODELS
    # ============================================================

    cars = [
        # Toyota
        CarModel(brand="Toyota", model="Camry", year_start=2018, year_end=2025,
                 tire_sizes="215/60R16,215/55R17,235/45R18",
                 wheel_pcd="5x114.3", wheel_et="45", wheel_dia="60.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Michelin Pilot Sport 4, Continental PremiumContact 6, Bridgestone Turanza T005, Nokian Hakka Blue 3"),
        CarModel(brand="Toyota", model="RAV4", year_start=2019, year_end=2025,
                 tire_sizes="225/65R17,225/55R18,235/55R19",
                 wheel_pcd="5x114.3", wheel_et="35", wheel_dia="60.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Michelin Latitude Sport 3, Continental CrossContact, Bridgestone Dueler H/P Sport"),
        CarModel(brand="Toyota", model="Corolla", year_start=2019, year_end=2025,
                 tire_sizes="195/65R15,205/55R16,225/45R17",
                 wheel_pcd="5x100", wheel_et="45", wheel_dia="54.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Bridgestone Turanza T005, Continental EcoContact 6, Michelin Energy Saver+"),

        # Kia
        CarModel(brand="Kia", model="Rio", year_start=2017, year_end=2025,
                 tire_sizes="185/65R15,195/55R16",
                 wheel_pcd="5x114.3", wheel_et="48", wheel_dia="56.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Nokian Hakka Green 3, Hankook Kinergy Eco 2, Continental EcoContact 6"),
        CarModel(brand="Kia", model="Sportage", year_start=2020, year_end=2025,
                 tire_sizes="215/65R16,215/55R17,225/50R18,235/45R19",
                 wheel_pcd="5x114.3", wheel_et="45", wheel_dia="56.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Michelin Primacy 4+, Continental PremiumContact 6, Pirelli Scorpion Verde All Season"),
        CarModel(brand="Kia", model="K5", year_start=2020, year_end=2025,
                 tire_sizes="205/60R16,215/55R17,235/45R18,245/40R19",
                 wheel_pcd="5x114.3", wheel_et="45", wheel_dia="56.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Michelin Pilot Sport 4, Continental PremiumContact 6, Hankook Ventus S1 evo3"),

        # Volkswagen
        CarModel(brand="Volkswagen", model="Polo", year_start=2020, year_end=2025,
                 tire_sizes="175/70R14,185/60R15,195/55R16",
                 wheel_pcd="5x100", wheel_et="44", wheel_dia="57.1",
                 bolt_thread="M14x1.5", bolt_type="bolt",
                 popular_tires="Continental EcoContact 6, Pirelli Cinturato P7, Michelin Energy Saver+"),
        CarModel(brand="Volkswagen", model="Tiguan", year_start=2018, year_end=2025,
                 tire_sizes="215/65R17,235/55R18,255/45R19",
                 wheel_pcd="5x112", wheel_et="44", wheel_dia="57.1",
                 bolt_thread="M14x1.5", bolt_type="bolt",
                 popular_tires="Michelin Primacy SUV+, Continental PremiumContact 6 SUV, Bridgestone Alenza 001"),

        # Skoda
        CarModel(brand="Skoda", model="Octavia", year_start=2020, year_end=2025,
                 tire_sizes="195/65R15,205/55R16,225/45R17,225/40R18",
                 wheel_pcd="5x112", wheel_et="49", wheel_dia="57.1",
                 bolt_thread="M14x1.5", bolt_type="bolt",
                 popular_tires="Continental PremiumContact 6, Michelin Pilot Sport 4, Goodyear Eagle F1 Asymmetric 5"),

        # Hyundai
        CarModel(brand="Hyundai", model="Solaris", year_start=2017, year_end=2025,
                 tire_sizes="185/65R15,195/55R16,205/50R17",
                 wheel_pcd="5x114.3", wheel_et="48", wheel_dia="56.1",
                 bolt_thread="M12x1.5", bolt_type="nut",
                 popular_tires="Nokian Hakka Green 3, Hankook Kinergy Eco 2, Bridgestone Turanza T005"),
    ]

    for car in cars:
        db.add_car(car)

    logger.info(f"✅ Добавлено {len(cars)} моделей авто")

    # ============================================================
    # REVIEWS
    # ============================================================

    camry = db.find_car("Toyota", "Camry", 2023)
    rio = db.find_car("Kia", "Rio", 2023)
    octavia = db.find_car("Skoda", "Octavia", 2023)

    reviews = [
        # Camry
        TireReview(car_id=camry.id, tire_name="Michelin Pilot Sport 4", tire_size="215/55R17",
                   rating=4.7, pros="тихие, отличное сцепление, износостойкие", cons="высокая цена",
                   text="Отличные шины. После 20000 км износ минимальный. Держат дорогу как летом, так и в дождь.",
                   source="drive2.ru", helpful_count=45),
        TireReview(car_id=camry.id, tire_name="Continental PremiumContact 6", tire_size="235/45R18",
                   rating=4.5, pros="комфортные, тихие, хорошая управляемость", cons="быстро изнашиваются на плохих дорогах",
                   text="Езжу второй сезон. По комфорту лучшие, но на ямах быстро убиваются.",
                   source="drive2.ru", helpful_count=32),
        TireReview(car_id=camry.id, tire_name="Bridgestone Turanza T005", tire_size="215/55R17",
                   rating=3.8, pros="цена/качество, износостойкость", cons="шумноваты на трассе",
                   text="Средние шины. Цена адекватная, но шумноваты на скорости выше 120.",
                   source="forum.toyota.ru", helpful_count=18),

        # Rio
        TireReview(car_id=rio.id, tire_name="Nokian Hakka Green 3", tire_size="185/65R15",
                   rating=4.6, pros="экономичные, тихие, хорошо держат мокрую", cons="мягковаты, боится ям",
                   text="Лучшие для Rio. Расход топлива упал на 0.5л. Но нужно объезжать ямы.",
                   source="drive2.ru", helpful_count=56),
        TireReview(car_id=rio.id, tire_name="Hankook Kinergy Eco 2", tire_size="185/65R15",
                   rating=4.2, pros="цена, экономичность, неплохая управляемость", cons="шумные на гравии",
                   text="Хороший бюджетный вариант. Для города отлично. На трассе чуть шумноваты.",
                   source="forum.kia.ru", helpful_count=28),

        # Octavia
        TireReview(car_id=octavia.id, tire_name="Continental PremiumContact 6", tire_size="225/45R17",
                   rating=4.6, pros="тишина, управляемость, комфорт", cons="цена",
                   text="Эталонные шины для Octavia. Тишина в салоне на любом покрытии.",
                   source="drive2.ru", helpful_count=34),
        TireReview(car_id=octavia.id, tire_name="Goodyear Eagle F1 Asymmetric 5", tire_size="225/45R17",
                   rating=4.4, pros="спортивные, отличное сцепление, информативность", cons="жёсткие, зимой опасно",
                   text="Для любителей активной езды. Но летом только, зимой — дубовые.",
                   source="forum.skoda.ru", helpful_count=22),
    ]

    for r in reviews:
        db.add_review(r)

    logger.info(f"✅ Добавлено {len(reviews)} отзывов")

    # ============================================================
    # PROBLEMS
    # ============================================================

    problems = [
        TireProblem(car_id=camry.id, tire_name="Bridgestone Turanza T005",
                    problem="Быстрый износ передних шин (10-15 тыс. км)",
                    severity="critical", source="forum.toyota.ru"),
        TireProblem(car_id=rio.id, tire_name="Bridgestone Turanza T005",
                    problem="Гул на скорости выше 90 км/ч",
                    severity="warning", source="forum.kia.ru"),
        TireProblem(car_id=octavia.id, tire_name="Pirelli Cinturato P7",
                    problem="Боковина трескается через 2 сезона",
                    severity="critical", source="forum.skoda.ru"),
        TireProblem(car_id=camry.id, tire_name="Nokian Hakka Blue 3",
                    problem="На мокрой трассе аквапланирование выше 110 км/ч",
                    severity="warning", source="drive2.ru"),
    ]

    for p in problems:
        db.add_problem(p)

    logger.info(f"✅ Добавлено {len(problems)} проблем")

    # ============================================================
    # SPECS
    # ============================================================

    specs = [
        TireSpec(name="Michelin Pilot Sport 4", category="sport", size="215/55R17",
                 load_index="94", speed_index="Y", noise_db=72.0,
                 fuel_class="C", wet_grip="A", tread_depth=7.2, runflat=False, ev_compatible=False),
        TireSpec(name="Continental PremiumContact 6", category="comfort", size="225/45R17",
                 load_index="94", speed_index="Y", noise_db=70.0,
                 fuel_class="B", wet_grip="A", tread_depth=7.5, runflat=False, ev_compatible=True),
        TireSpec(name="Nokian Hakka Green 3", category="economical", size="185/65R15",
                 load_index="88", speed_index="H", noise_db=69.0,
                 fuel_class="A", wet_grip="B", tread_depth=8.0, runflat=False, ev_compatible=False),
        TireSpec(name="Bridgestone Turanza T005", category="standard", size="215/55R17",
                 load_index="94", speed_index="V", noise_db=71.0,
                 fuel_class="C", wet_grip="A", tread_depth=7.8, runflat=False, ev_compatible=False),
    ]

    for s in specs:
        db.add_spec(s)

    logger.info(f"✅ Добавлено {len(specs)} ТТХ шин")

    # Итог
    stats = db.stats()
    logger.info(f"📊 Итого: {stats['cars']} авто, {stats['reviews']} отзывов, БД {stats['db_size_mb']} MB")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    seed()
