"""Тесты схемы БД"""
import os
import tempfile


def _make_db():
    """Создаёт DatabaseService c временным файлом (не :memory:)."""
    from app.services.database.schema import DatabaseService
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db = DatabaseService(tmp.name)
    return db, tmp.name


class TestDatabaseSchema:
    def test_create_tables(self):
        from app.services.database.schema import DatabaseService, DB_PATH
        db, path = _make_db()
        try:
            with db._conn() as conn:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
                table_names = [t['name'] for t in tables]

                assert 'car_models' in table_names
                assert 'tire_reviews' in table_names
                assert 'tire_problems' in table_names
                assert 'tire_specs' in table_names
                # user_profiles — из user_history.py, не обязательна здесь
        finally:
            os.unlink(path)

    def test_car_models_columns(self):
        from app.services.database.schema import DatabaseService
        db, path = _make_db()
        try:
            with db._conn() as conn:
                cols = [r['name'] for r in conn.execute("PRAGMA table_info('car_models')").fetchall()]
                assert 'brand' in cols
                assert 'model' in cols
                assert 'tire_sizes' in cols
                assert 'wheel_pcd' in cols
        finally:
            os.unlink(path)

    def test_add_and_find_car(self):
        from app.services.database.schema import DatabaseService, CarModel
        db, path = _make_db()
        try:
            car = CarModel(brand="TestBrand", model="TestModel", year_start=2020, year_end=2025)
            car_id = db.add_car(car)
            assert car_id > 0

            found = db.find_car("TestBrand", "TestModel", 2023)
            assert found is not None
            assert found.brand == "TestBrand"
            assert found.model == "TestModel"
        finally:
            os.unlink(path)

    def test_get_brands(self):
        from app.services.database.schema import DatabaseService, CarModel
        db, path = _make_db()
        try:
            db.add_car(CarModel(brand="Toyota", model="Camry"))
            db.add_car(CarModel(brand="BMW", model="X5"))
            brands = db.get_brands()
            assert 'Toyota' in brands
            assert 'BMW' in brands
        finally:
            os.unlink(path)

    def test_get_models(self):
        from app.services.database.schema import DatabaseService, CarModel
        db, path = _make_db()
        try:
            db.add_car(CarModel(brand="Toyota", model="Camry"))
            db.add_car(CarModel(brand="Toyota", model="Corolla"))
            models = db.get_models("Toyota")
            assert 'Camry' in models
            assert 'Corolla' in models
        finally:
            os.unlink(path)

    def test_add_review(self):
        from app.services.database.schema import DatabaseService, CarModel, TireReview
        db, path = _make_db()
        try:
            car_id = db.add_car(CarModel(brand="Test", model="Test"))
            review = TireReview(
                car_id=car_id,
                tire_name="Michelin Pilot Sport 4",
                rating=4.5,
                pros="тихие, износостойкие",
                cons="дорогие"
            )
            review_id = db.add_review(review)
            assert review_id > 0
            reviews = db.get_reviews(car_id)
            assert len(reviews) == 1
            assert reviews[0].tire_name == "Michelin Pilot Sport 4"
        finally:
            os.unlink(path)

    def test_add_spec(self):
        from app.services.database.schema import DatabaseService, TireSpec
        db, path = _make_db()
        try:
            spec = TireSpec(
                name="Michelin Pilot Sport 4",
                category="sport",
                size="225/45R17",
                load_index="91",
                speed_index="Y",
                noise_db=72.0,
                runflat=False,
                ev_compatible=False
            )
            spec_id = db.add_spec(spec)
            assert spec_id > 0
            found = db.get_spec("Michelin Pilot Sport 4")
            assert found is not None
            assert found.category == "sport"
        finally:
            os.unlink(path)

    def test_stats(self):
        from app.services.database.schema import DatabaseService
        db, path = _make_db()
        try:
            stats = db.stats()
            assert 'cars' in stats
            assert 'reviews' in stats
        finally:
            os.unlink(path)

    def test_search_reviews(self):
        from app.services.database.schema import DatabaseService, CarModel, TireReview
        db, path = _make_db()
        try:
            car_id = db.add_car(CarModel(brand="Test", model="Test"))
            db.add_review(TireReview(car_id=car_id, tire_name="GoodYear", text="очень тихие шины"))
            db.add_review(TireReview(car_id=car_id, tire_name="Michelin", text="дорогие но качественные"))
            results = db.search_reviews("тихие")
            assert len(results) >= 1
        finally:
            os.unlink(path)

    def test_get_problems(self):
        from app.services.database.schema import DatabaseService, CarModel, TireProblem
        db, path = _make_db()
        try:
            car_id = db.add_car(CarModel(brand="Test", model="Test"))
            db.add_problem(TireProblem(car_id=car_id, tire_name="TireX", problem="шумная", severity="warning"))
            problems = db.get_problems(car_id)
            assert len(problems) == 1
            assert problems[0].problem == "шумная"
        finally:
            os.unlink(path)

    def test_enhance_prompt_without_data(self):
        from app.services.database.schema import DatabaseService
        db, path = _make_db()
        try:
            result = db.enhance_prompt("UnknownBrand", "UnknownModel", 2023)
            assert result == ""
        finally:
            os.unlink(path)
