"""Тесты RAG"""
from app.services.rag.knowledge_base import KnowledgeBase


class TestKnowledgeBase:
    def test_init(self):
        kb = KnowledgeBase()
        assert kb is not None

    def test_get_popular_tires(self):
        kb = KnowledgeBase()
        tires = kb.get_popular_tires("Toyota", "Camry", 2020)
        assert isinstance(tires, list)

    def test_get_tire_sizes(self):
        kb = KnowledgeBase()
        sizes = kb.get_tire_sizes("Toyota", "Camry", 2020)
        assert isinstance(sizes, list)

    def test_get_compatibility(self):
        kb = KnowledgeBase()
        compat = kb.get_compatibility("Michelin", "Pilot Sport 4", 2020)
        # Может быть None если данных нет — это нормально
        assert compat is None or isinstance(compat, str)

    def test_get_reviews(self):
        kb = KnowledgeBase()
        reviews = kb.get_reviews("Michelin", "Pilot Sport 4")
        assert isinstance(reviews, list)

    def test_get_problems(self):
        kb = KnowledgeBase()
        problems = kb.get_problems("Michelin", "Pilot Sport 4")
        assert isinstance(problems, list)

    def test_enhance_prompt(self):
        kb = KnowledgeBase()
        enhanced = kb.enhance_prompt("Toyota", "Camry", 2020)
        assert enhanced is not None
        assert isinstance(enhanced, str)
