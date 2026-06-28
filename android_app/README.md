# Авто Эксперт AI — Android-приложение (Flutter + RuStore)

## 🚀 Быстрый старт

```bash
# 1. Установите Flutter
# https://docs.flutter.dev/get-started/install

# 2. Перейдите в папку приложения
cd android_app

# 3. Установите зависимости
flutter pub get

# 4. Запустите на устройстве/эмуляторе
flutter run

# 5. Сборка APK для RuStore
flutter build apk --release
# APK будет в: build/app/outputs/flutter-apk/app-release.apk

# 6. Сборка App Bundle (рекомендуется для RuStore)
flutter build appbundle --release
# AAB будет в: build/app/outputs/bundle/release/app-release.aab
```

## 🏗️ Структура проекта

```
android_app/
├── lib/
│   ├── main.dart              # Точка входа, глобальное состояние
│   ├── screens/
│   │   ├── home_screen.dart    # Главный экран (чат/форма)
│   │   ├── form_screen.dart    # Экран быстрой формы
│   │   ├── chat_screen.dart    # Полноэкранный чат
│   │   └── result_screen.dart  # Результаты подбора
│   ├── widgets/
│   │   └── product_card.dart   # Карточка товара
│   ├── services/
│   │   └── api_service.dart    # HTTP клиент к API
│   └── models/
│       (модели в main.dart)
├── android/
│   └── app/src/main/
│       └── AndroidManifest.xml
├── ios/                        # iOS пока не требуется
├── pubspec.yaml
└── README.md
```

## 🔗 API

Приложение использует бэкенд на `http://10.0.2.2:8000` (Android эмулятор).

Для **реального устройства** замените IP в `lib/services/api_service.dart`:
```dart
static const String _baseUrl = 'http://ВАШ_IP:8000';
```

## 📦 Публикация на RuStore

1. Соберите AAB: `flutter build appbundle --release`
2. Зайдите на https://console.rustore.ru
3. Создайте новое приложение
4. Загрузите `app-release.aab`
5. Заполните описание, скриншоты
6. Отправьте на модерацию

## 🎨 Тема

Тёмная тема "Carbon" с акцентным цветом `#00D4FF` (циан) и `#FF6B35` (оранжевый).

Поддерживаемые функции:
- ✅ Чат с AI-консультантом
- ✅ Форма быстрого подбора
- ✅ Голосовой ввод (микрофон)
- ✅ Результаты с ценами
- ✅ Telegram Mini App интеграция (через WebView)
