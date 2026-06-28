# Сборка Android приложения "Авто Эксперт AI"

## Требования

- **Flutter SDK** 3.1.0 или новее (рекомендуется 3.10+)
- **Android Studio** или **Android SDK** (API 34+)
- **JDK 17+**

## Структура проекта

```
android_app/
├── lib/
│   ├── main.dart                  # Точка входа, AppState (глобальное состояние)
│   ├── services/
│   │   └── api_service.dart       # HTTP клиент для API
│   ├── screens/
│   │   ├── home_screen.dart       # Главный экран (чат + форма)
│   │   ├── chat_screen.dart       # Отдельный экран чата
│   │   ├── form_screen.dart       # Экран формы подбора
│   │   └── result_screen.dart     # Экран результатов
│   └── widgets/
│       └── product_card.dart      # Карточка товара
├── assets/
│   ├── animations/                # Lottie анимации (JSON)
│   └── images/                    # Изображения
├── android/                       # Android нативный код
├── pubspec.yaml                   # Зависимости
└── BUILD_INSTRUCTIONS.md          # Этот файл
```

## Шаги сборки

### 1. Установите зависимости

```bash
cd android_app
flutter pub get
```

### 2. Проверьте конфигурацию Android

Убедитесь, что в `android_app/android/app/src/main/AndroidManifest.xml` указан правильный `package` (по умолчанию: `com.garagemind.avtoexpert`).

### 3. Соберите APK

**Debug APK (для тестирования):**
```bash
flutter build apk --debug
```

**Release APK (для установки):**
```bash
flutter build apk --release
```

**App Bundle (для Google Play):**
```bash
flutter build appbundle --release
```

### 4. Готовый APK

После сборки APK будет здесь:
```
build/app/outputs/flutter-apk/app-release.apk
```

## Настройка API

По умолчанию приложение стучится на `http://10.0.2.2:8000` (локальный сервер для эмулятора Android).

Для реального устройства:
1. Откройте `lib/services/api_service.dart`
2. Измените `_baseUrl` на IP вашего сервера:
   ```dart
   static const String _baseUrl = 'http://ВАШ_IP:8000';
   ```

## Возможные проблемы

### `telegram_webapp` не найден
Если ошибка про `telegram_webapp` — он уже удалён из pubspec.yaml, всё должно работать.

### `google_fonts` требует интернет
Пакет Google Fonts при первом запуске загружает шрифты. Если интернета нет, добавьте в pubspec.yaml:
```yaml
  google_fonts: ^6.1.0
```
Он будет использовать кэшированные шрифты при офлайн-сборке.

### Ошибка Gradle
Если Gradle не может синхронизироваться:
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter build apk --debug
```

## Запуск без сборки (на эмуляторе)

```bash
flutter run
```

Это установит и запустит приложение на подключённом устройстве/эмуляторе.

---

**Готово!** 🚀 Приложение "Авто Эксперт AI" — это Flutter-клиент для подбора шин с AI-консультантом.
