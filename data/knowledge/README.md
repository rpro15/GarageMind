# 🧠 База знаний GarageMind AI

## Структура

```
data/knowledge/
├── reviews/        # Отзывы владельцев (парсинг форумов)
├── compatibility/  # Совместимость шин/дисков с авто
├── problems/       # Частые проблемы и жалобы
└── specs/          # Технические характеристики
```

## Формат

### review.json
```json
{
  "id": "rev_001",
  "source": "drive2",
  "car": "Kia Rio 2020",
  "tire": "Nokian Hakka Green 185/65 R15",
  "rating": 4.5,
  "pros": ["тихие", "экономичные", "хорошо держат мокрую"],
  "cons": ["дороговаты"],
  "text": "Купил в 2023...",
  "date": "2023-10-15"
}
```

### compatibility.json
```json
{
  "car": "Toyota Camry 2024",
  "tire_sizes": ["215/55 R17", "235/45 R18"],
  "popular_tires": [
    "Michelin Pilot Sport 4",
    "Continental PremiumContact 6",
    "Nokian Hakka Blue 3"
  ],
  "wheel_params": {
    "pcd": "5x114.3",
    "et": 45,
    "dia": 60.1,
    "bolt": "M12x1.5"
  }
}
```
