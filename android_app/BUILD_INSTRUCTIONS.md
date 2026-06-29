# 🚗 Авто Эксперт AI — Android App

## 📱 Сборка

### Требования
- Flutter SDK 3.1.0+
- Android Studio / Xcode
- Подключённый Android-девайс или эмулятор

### Запуск
```bash
cd android_app
flutter pub get
flutter run
```

### Сборка APK
```bash
flutter build apk --release
# Файл: build/app/outputs/flutter-apk/app-release.apk
```

### Сборка App Bundle (Google Play)
```bash
flutter build appbundle --release
# Файл: build/app/outputs/bundle/release/app-release.aab
```

## 🔗 API
Приложение обращается к серверу по адресу `http://10.0.2.2:8000/api`  
(стандартный localhost для Android эмулятора).

Для реального устройства замените на IP вашего сервера в `lib/services/api_service.dart`.

## 📁 Структура проекта
```
lib/
├── main.dart                          # Точка входа
├── models/
│   ├── car_brand.dart                 # Модель бренда
│   ├── tire_request.dart              # Запрос на подбор
│   └── product.dart                   # Товар и результат
├── providers/
│   └── app_provider.dart              # State management
├── services/
│   ├── api_service.dart              # HTTP клиент
│   └── localization_service.dart     # Локализация
├── screens/
│   ├── home_screen.dart              # Главный экран
│   ├── chat_screen.dart              # Чат режим
│   ├── form_screen.dart              # Форма режим
│   └── result_screen.dart            # Результаты
└── widgets/
    ├── header_widget.dart            # Шапка
    └── product_card.dart             # Карточка товара
assets/
├── lang/
│   ├── ru.json                       # Русский язык
│   └── en.json                       # English
├── animations/                       # Lottie анимации
└── images/                           # Изображения
```
